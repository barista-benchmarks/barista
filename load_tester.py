"""Performs load-testing on applications.

Posesses the ability of load-testing both JVM based applications as well as native applications.
The load-testing is performed using the Barista harness, which carries out 3 distinct periods: warmup, throughput and latency measurements.
Each one of these periods is highly configurable.
"""

from wrk2_load_generator import Wrk2LoadGenerator
from wrk1_load_generator import Wrk1LoadGenerator
from abstract_load_generator import cmd_exists
import subprocess
import os
import time
import logging as log
import traceback
import uuid
import itertools
import process_info
import sys
import datetime
from http.client import HTTPConnection, HTTPSConnection
from concurrent_reader import ConcurrentReader
from configuration import ServiceMode
from results import results_to_csv, compile_usage_p_values, dump_result_json
from logging_formatting import log_throughput, log_latency, log_startup, log_memory_usage, log_cpu_percent
from throughput_explorer import ThroughputExplorer


class Benchmark:
    """Implements the full pipeline of the benchmark."""
    def __init__(self, config):
        self._config = config
        #Change this for throughput measures
        self._output_folder = self._config.output_folder
        self._warmup = Wrk1LoadGenerator(self._config._warmup, self._output_folder, self._config.endpoint)
        self._latency_benchmark = Wrk2LoadGenerator(self._config.latency, self._output_folder, self._config.endpoint)
        self._throughput_benchmark = Wrk1LoadGenerator(self._config.throughput, self._output_folder, self._config.endpoint)
        self._app_output = ""
        self._results = None

    @property
    def config(self):
        return self._config

    def run(self):
        """
        Executes the full pipeline of the benchmark.
         1. Startup
         2. Measure
         3. Cleanup
        """
        result = None
        app_terminated_early = False
        try:
            self._start_app()

            # Run all the benchmark phases
            startup_data = self._run_startup()
            warmup_data = self._run_warmup()
            throughput_data = self._run_throughput()
            latency_data = self._run_latency(throughput_data)

            result = self._compile_results(startup_data, warmup_data, throughput_data, latency_data, self._concurrent_reader)
        except AppProcessFinishedUnexpectedly as e:
            app_terminated_early = True
            raise e
        except Exception as e:
            log.error("Exception caught in main benchmark pipeline")
            log.error(traceback.format_exc())
        finally:
            log.info("Benchmark done")
            if not app_terminated_early:
                self._cleanup()
                self._save_results(result)

    def _start_app(self):
        """Starts the app process."""
        log.info(self.config.describe())

        command = []
        cmd_app_prefix_length = 0
        # Check if cmd_app_prefix is defined
        if self.config.cmd_app_prefix is not None:
            cmd_app_prefix_length = len(self.config.cmd_app_prefix)
            command += self.config.cmd_app_prefix

        if self.config.mode == ServiceMode.JVM:
            # JVM Case
            java_exe = self.config.java_home
            if java_exe is not None:
                java_exe = java_exe + '/bin/java'
                command += [java_exe]
            else:
                # try java command if no java set
                log.warning("JAVA_HOME not set. Trying java!")
                if cmd_exists('java'):
                    command +=  ['java']
                else:
                    raise ValueError("java command not found. Please set JAVA home or have java in your path")
            command += self.config.vm_options
            if len(self.config.app_executable) > 4 and self.config.app_executable[-4:] =='.jar':
                command += ['-jar', self.config.app_executable]
            else:
                command += [self.config.app_executable]
            command += self.config.app_args
        elif self.config.mode == ServiceMode.NATIVE:
            # Native case
            command += [self.config.app_executable]
            command += self.config.vm_options
            command += self.config.app_args
            log.info(f"Executing command:\n{' '.join(command)}")
        else:
            # Other case/ Check for bad cases
            raise ValueError(f"{self.config.mode} flag not supported")

        log.info(f"Starting microservice with:\n{' '.join(command)}")
        self._app_command = command[cmd_app_prefix_length:]
        self._root_process = subprocess.Popen(command, start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell = False)

        app_pid = self._find_cmdline_proc_in_tree(self._root_process.pid, self._app_command)
        self._app_process = process_info.get_process(app_pid)
        log.info(f"Detected app process (pid={self._app_process.pid}) with command-line:\n{' '.join(self._app_process.cmdline())}")

        self._concurrent_reader = ConcurrentReader(self._root_process, self._app_process, self.config.resource_usage_polling_interval)
        self._concurrent_reader.start()

    def _run_startup(self):
        """Runs the startup phase of the benchmark process."""
        if self.config.startup.request_count <= 0:
            log.info("No startup required, skipping startup...")
            return

        startup_data = []
        log.info(f"Running startup measurements: sending {self.config.startup.request_count} GET request(s) to {self.config.endpoint_protocol}://{self.config.endpoint_domain}:{self.config.endpoint_port}{self.config.endpoint_path}")
        for request_idx in range(self.config.startup.request_count):
            ts_before_request = time.perf_counter()
            self._request_until_response(self.config.startup.timeout)
            response_time = (time.perf_counter() - ts_before_request) * 1000
            log.info(f"Received response #{request_idx + 1} in {response_time:6.2f} ms")
            startup_data.append({
                "response_time": response_time,
                "iteration": request_idx,
            })
        return startup_data

    def _request_until_response(self, timeout):
        """Repeatedly pings the app endpoint until there is a response.

        Periodically checks whether the application process is still running, raising an exception if the process terminated
        or if the timeout period passes before a response is received.

        :param number timeout: The timeout period in seconds. A 0 value means the method should never timeout.
        """
        poll_interval = 1
        ts_start = time.perf_counter()
        ts_last_poll = ts_start
        while (True):
            try:
                if self.config.endpoint_protocol == "http":
                    conn = HTTPConnection(self.config.endpoint_domain, self.config.endpoint_port)
                else:
                    conn = HTTPSConnection(self.config.endpoint_domain, self.config.endpoint_port)
                conn.request("GET", self.config.endpoint_path)
                res = conn.getresponse()
                if res.status < 500:
                    log.debug(f"App responded {res.status} after startup")
                    break
                else :
                    log.warning(f"App responded {res.status}. Stopping and cleaning up")
                    self._cleanup()
            except ConnectionRefusedError:
                ts_current = time.perf_counter()
                if ts_current - ts_last_poll >= poll_interval:
                    # Time for a periodic check of the app process status
                    return_code = self._root_process.poll()
                    if return_code is not None:
                        raise AppProcessFinishedUnexpectedly(f"Root process exited unexpectedly with return code {return_code}!")
                if timeout != 0 and ts_current - ts_start >= timeout:
                    raise TimeoutError(f"App '{self.config.bench_name}' unresponsive! Could not get a response after trying for {timeout} seconds!")
                time.sleep(0.001)

    def _run_warmup(self):
        """Runs the warmup phase of the benchmark process."""
        results = []
        for script, i in self._get_iterations(self.config.warmup.script, self.config.warmup.iteration_count):
            log.info(f"Running warmup iteration {i+1}/{self.config.warmup.iteration_count}")
            warmup_measurement = self._warmup.measure(script)
            results.append(self._format_throughput_measurement(warmup_measurement, i, script))
            self._warmup.dump_stdout(self._output_folder, warmup_measurement['stdout'], f"warmup-{i+1}")
        return results

    def _run_throughput(self):
        """Execute the throughput phase of the benchmark."""
        results = []
        for script, i in self._get_iterations(self.config.throughput.script, self.config.throughput.iteration_count):
            log.info(f"Running throughput iteration {i+1}/{self.config.throughput.iteration_count}")
            throughput_result_map = self._throughput_benchmark.measure(script)
            results.append(self._format_throughput_measurement(throughput_result_map, i, script))
            self._throughput_benchmark.dump_stdout(self._output_folder, throughput_result_map['stdout'], f"throughput-{i+1}")
        return results

    def _run_latency(self, throughput_data):
        """Execute the latency phase of the benchmark."""
        latency_manager = ThroughputExplorer(self.config.latency, self._output_folder, self.config.endpoint, throughput_data)
        results = latency_manager.explore()
        return results

    def _dump_stdout(self):
        """Dumps the application standard output to a file."""
        final_application_output = self._concurrent_reader.output

        if not final_application_output:
            log.warning("No application output was captured!")
            return

        log.info(f"Dumping application outputs to: {self._output_folder}/app-dump.txt")
        with open(f"{self._output_folder}/app-dump.txt", "w") as file:
            file.write(final_application_output)

    def _get_iterations(self, scripts, iterations_per_script):
        """Gets the iterations to be executed over all scripts.

        :param list scripts: List of scripts, where each script should be executed iterations_per_script times.
        :param number iterations_per_script: Number of iterations that should be executed for each script.
        :return: Returns a list of iteration information, the information for each iteration comprising the script to be executed and the iteration index (script x iteration index).
        :rtype: list
        """
        scripts = scripts if scripts is not None else [None]
        iterations = range(iterations_per_script)
        return list(itertools.product(scripts, iterations))

    def _format_throughput_measurement(self, result, iteration_num, script):
        """Appends the information on iteration index, script name, and load-testing command to the iteration results.

        :param dict result: Dictionary containing information about the load-testing iteration. Contains the command used and the obtained results.
        :param number iteration_num: Measurement iteration index.
        :param string script: Name of the script that was executed in the iteration.
        :return: Iteration result dictionary updated to contain script, iteration index, and command information.
        :rtype: dict
        """
        datapoint = result['throughput'].copy()
        datapoint['command'] = result['command']
        datapoint['iteration'] = iteration_num
        if script is not None:
            datapoint['script'] = os.path.basename(script)
        return datapoint

    def _find_cmdline_proc_in_tree(self, root_pid, cmdline):
        """Finds the process ID of the process matching the command-line in the process tree of the root process.

        Repeatedly scans through the process tree of the root process trying to match the command-line.
        The lookup is repeated until a time limit is exceeded, at which point all of the processes in
        the process tree are terminated and an exception is raised. Repeating is necessary to allow the
        root process (see option '--cmd-app-prefix') to perform its setup before starting the app process.

        :param number root_pid: Process ID of the root of the process tree which should be searched.
        :param list cmdline: Command-line of the process to be found.
        :return: Process ID of the searched for process.
        :rtype: number
        """
        start_time = time.time()
        # very generous maximum time for the root process to start the app process, in seconds
        root_process_startup_time_limit = 5.0
        # time between lookup attempts, in seconds
        retry_grace = 0.001

        tree_root = process_info.get_process(root_pid)
        while time.time() < start_time + root_process_startup_time_limit:
            try:
                proc_tree = [tree_root] + tree_root.children(recursive=True)
                # Look for exact match
                for p in proc_tree:
                    if p.cmdline() == cmdline:
                        return p.pid
                # Look for executable match
                for p in proc_tree:
                    process_cmdline = p.cmdline()
                    if len(process_cmdline) > 0 and process_cmdline[0] == cmdline[0]:
                        return p.pid
            except (FileNotFoundError, ProcessLookupError):
                pass
            # Sleep before retrying
            time.sleep(retry_grace)
        # Terminate every process
        log.error("Terminating all spawned processes!")
        for p in proc_tree:
            p.terminate()
        raise AppProcessFinishedUnexpectedly(f"Could not find app process using expected cmdline: \"{' '.join(cmdline)}\"! Terminated all spawned processes!")

    def _cleanup(self):
        """Cleans up the acquired resources: terminates the app process, which should terminate all other spawned processes."""
        if self._latency_benchmark is not None:
            self._latency_benchmark.cleanup()
        if self._throughput_benchmark is not None:
            self._throughput_benchmark.cleanup()
        if self._root_process is not None:
            root_process_return_code = self._root_process.poll()
            if root_process_return_code is not None:
                raise AppProcessFinishedUnexpectedly(f"Root process terminated prematurely with return code {root_process_return_code}!")
            self._app_process.terminate()
        if self._concurrent_reader is not None:
            self._concurrent_reader.join()

    def _compile_results(self, startup_data, warmup_data, throughput_data, latency_data, concurrent_reader):
        """Constructs a dictionary containing all of the data gathered by the Barista harness.

        Constructs a dictionary containing the results of all the benchmark phases,
        as well as the resource usage recorded during the benchmark. The resource usage data is added to the
        dictionary both as raw and percentile values.

        :param list startup_data: Results of the startup phase of the benchmark.
        :param list warmup_data: Results of the warmup phase of the benchmark.
        :param list throughput_data: Results of the throughput phase of the benchmark.
        :param dict latency_data: Results of the latency phase of the benchmark.
        :param ConcurrentReader concurrent_reader: The thread that recorded resource usage during the benchmark.
        :return: All of the data gathered by the Barista harness.
        :rtype: dict
        """
        rss_p_values, vms_p_values, cpu_p_values = [], [], []
        usage_data = list(concurrent_reader.resources)
        if usage_data:
            rss_p_values, vms_p_values, cpu_p_values = compile_usage_p_values(usage_data)
        return {
            "benchmark": self.config.bench_name,
            "command": sys.argv,
            "timestamp": f"{datetime.datetime.now()}",
            "startup": {
                "id": self._create_unique_id(),
                "measurements": startup_data,
                "self_reported": concurrent_reader.startup_times,
            },
            "warmup": {
                "id": self._create_unique_id(),
                "measurements": warmup_data,
            },
            "throughput": {
                "id": self._create_unique_id(),
                "measurements": throughput_data,
            },
            "latency": {
                "id": self._create_unique_id(),
                "measurements": latency_data,
            },
            "resource_usage": {
                "rss": rss_p_values,
                "vms": vms_p_values,
                "cpu": cpu_p_values,
                "raw": usage_data,
            },
        }

    def _create_unique_id(self):
        return str(uuid.uuid4())[:8]

    def print_final_report_to_stdout(self):
        if self._results is None:
            raise ValueError("No result data to include in the final report!")

        log.info("================================================================================")
        log.info(f"Barista report for benchmark '{self._results['benchmark']}'")
        log.info(f"Run command: python3 {' '.join(self._results['command'])}")

        if self._results['resource_usage'] and (self._results['resource_usage']['rss'] or self._results['resource_usage']['vms'] or self._results['resource_usage']['cpu']):
            log.info("Resource usage results:")
            if self._results['resource_usage']['rss']:
                log.info("\tResident Set Size:")
                log_memory_usage(self._results['resource_usage']['rss'])
            if self._results['resource_usage']['vms']:
                log.info("\tVirtual Memory Size:")
                log_memory_usage(self._results['resource_usage']['vms'])
            if self._results['resource_usage']['cpu']:
                log.info("\tSystem-wide CPU utilization:")
                log_cpu_percent(self._results['resource_usage']['cpu'])

        if self._results['startup'] and self._results['startup']['measurements']:
            log.info("Startup results:")
            log_startup(self._results['startup']['measurements'])

        if self._results['warmup'] and self._results['warmup']['measurements']:
            log.info("Warmup results:")
            for i in range(self.config.warmup.iteration_count):
                log_throughput(self._results['warmup']['measurements'][i], i+1)

        if self._results['throughput'] and self._results['throughput']['measurements']:
            log.info("Throughput results: ")
            for i in range(self.config.throughput.iteration_count):
                log_throughput(self._results['throughput']['measurements'][i], i+1)

        if self._results['latency'] and self._results['latency']['measurements']:
            log.info("Latency results: ")
            for name, measurements in self._results['latency']['measurements'].items():
                log.info(f"Results of {name} latency measurement")
                for i in range(self.config.latency.iteration_count):
                    log_latency(measurements[i], i+1)
        log.info("================================================================================")

    def _save_results(self, result):
        """Saves the measurement results, usage stats, and application output to files."""
        if not result:
            raise ValueError("Results have not been compiled successfully!")

        self._results = result
        dump_result_json(self._output_folder, result)
        results_to_csv(self._output_folder, result)
        self._dump_stdout()

class AppProcessFinishedUnexpectedly(Exception):
    """Used to denote an unexpected termination of the application process."""
    pass