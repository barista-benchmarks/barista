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
import logging as log
import traceback
import uuid
import itertools
import sys
import datetime
from app_manager import AppProcessFinishedUnexpectedly
from startup_manager import StartupManager
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
        self._startup_manager = StartupManager(self._config)
        self._warmup = Wrk1LoadGenerator(self._config._warmup, self._output_folder, self._config.endpoint)
        self._latency_benchmark = Wrk2LoadGenerator(self._config.latency, self._output_folder, self._config.endpoint)
        self._throughput_benchmark = Wrk1LoadGenerator(self._config.throughput, self._output_folder, self._config.endpoint)
        self._app_output = ""
        self._concurrent_reader = None
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
            log.info(self.config.describe())

            # Run all the benchmark phases
            startup_data = self._run_startup()
            warmup_data = self._run_warmup()
            throughput_data = self._run_throughput()
            latency_data = self._run_latency(throughput_data)

            result = self._compile_results(startup_data, warmup_data, throughput_data, latency_data, self._concurrent_reader)
            self._save_results(result)
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

    def _run_startup(self):
        startup_data = self._startup_manager.run()
        root_process = self._startup_manager.app_manager.root_process
        app_process = self._startup_manager.app_manager.app_process
        self._concurrent_reader = ConcurrentReader(root_process, app_process, self.config.resource_usage_polling_interval)
        self._concurrent_reader.start()
        return startup_data

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

    def _cleanup(self):
        """Cleans up the acquired resources: terminates the app process, which should terminate all other spawned processes."""
        if self._latency_benchmark is not None:
            self._latency_benchmark.cleanup()
        if self._throughput_benchmark is not None:
            self._throughput_benchmark.cleanup()
        self._startup_manager.kill_app()
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
