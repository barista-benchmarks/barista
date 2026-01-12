import subprocess
import re
import logging as log
from abstract_wrk_load_generator import AbstractWrkLoadGenerator
from abstract_load_generator import cmd_exists

class Wrk2LoadGenerator(AbstractWrkLoadGenerator):
    def __init__(self, config, output_dir, endpoint, request_rate=100000):
        self._endpoint = endpoint
        self._config = config
        self._output_dir = output_dir
        self._request_rate = request_rate
        self._threads = config.threads
        self._connections = config.connections

    def measure(self, rate=None, duration=None, script=None):
        if not cmd_exists("wrk2"):
            raise FileNotFoundError("wrk2 command not found please set it in PATH.")

        has_rate, version_output = self.wrk2_has_rate()
        if not has_rate:
            raise FileNotFoundError(
                "wrk2 should have --rate flag. Please ensure you have wrk2 alias not for wrk.\n"
                f"Output of 'wrk2 --version':\n{version_output}"
            )

        if duration is None:
            duration = self._config.iteration_duration
        
        if rate is None:
            rate = 100000
            log.warning(f"No rate was given. Setting rate to {rate} op/s")

        log.info("Begining to measure latency")
        command = ["wrk2","-d", f"{duration}s", "-R", f"{rate}", "--latency", self._endpoint, "-t", f"{self._threads}", "-c", f"{self._connections}"]
        if script is not None:
            command += ['--script', script]
            # Propagate the number of threads to the Lua script
            # This enables the Lua script to e.g. split the workload into <thread_count> segments
            command += ["--", f"{self._threads}"]
        log.info(f"Running latency command:\n{' '.join(command)}")
        self._wrk_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell = False)
        self._wrk_process.wait()
        log.info("Finished measuring latency")
        output = self._wrk_process.communicate()[0].decode("utf-8")
        p_vals = self.parse_latencies(output)

        exit_code = self._wrk_process.returncode
        if exit_code == 0:
            return {"p_values": p_vals,
                    "command": ' '.join(command),
                    "stdout": output,
                    "exit_code": exit_code}
        self.crash_dump(self._output_dir, output)
        raise ValueError(f"Latency command failed and exited with: {exit_code}")
    
    def cleanup(self):
        log.debug("no cleanup needed for wrk2 load generator")

    def wrk2_has_rate(self):
        wrk = subprocess.Popen(['wrk2', '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        wrk.wait()
        output = wrk.communicate()[0].decode("utf-8")
        return ('--rate' in output, output)

    def parse_latencies(self, output):
        latency = " *(\d+\.?\d*)% +(\d+\.?\d*)(\w+)"
        parsed = {}
        for matches in re.findall(latency, output):
            percentile, number, unit = matches
            parsed[float(percentile)] = round(float(number) * self.time_unit_to_ms(unit), 9)
        return parsed

    def time_unit_to_ms(self, unit):
        if unit == 'ms':
            return 1
        elif unit == 'us':
            return 1/ 1000
        elif unit == 's':
            return 1000
        elif unit == 'm':
            return 60000
        elif unit == 'h':
            return 3600000
        else:
            raise ValueError(f"Unable to parse time unit from: {unit}")

    def parse_measurements(self, measurement):
        log.info("Parsing received measurements for latency")
        return self.load_parser(measurement)['latency']