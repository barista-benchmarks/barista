import subprocess
import logging as log
from abstract_wrk_load_generator import AbstractWrkLoadGenerator
from abstract_load_generator import cmd_exists

class Wrk1LoadGenerator(AbstractWrkLoadGenerator):
    def __init__(self, config, output_dir, endpoint):
        self._endpoint = endpoint
        self._duration = config.iteration_duration
        self._output_dir = output_dir
        self._threads = config.threads
        self._connections = config.connections

    def measure(self, script=None):
        if not cmd_exists("wrk"):
            raise FileNotFoundError("wrk command not found in PATH.")
        
        if self.wrk_has_rate():
            raise FileNotFoundError("wrk should not have --rate flag. Please ensure you have wrk alias not for wrk2")

        log.info("Begining to measure throughput")
        command = ["wrk","-d", f"{self._duration}s", self._endpoint, "-t", f"{self._threads}", "-c", f"{self._connections}"]
        if script is not None:
            command += ['--script', script]
            # Propagate the number of threads to the Lua script
            # This enables the Lua script to e.g. split the workload into <thread_count> segments
            command += ["--", f"{self._threads}"]
        log.info(f"Measuring throughput with :\n{' '.join(command)}")
        self._wrk_processs = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell = False)
        self._wrk_processs.wait()
        output = self._wrk_processs.communicate()[0].decode("utf-8")
        exit_code = self._wrk_processs.returncode

        if exit_code == 0:
            return {
                    "throughput":self.parse_measurements(output),
                    "command": ' '.join(command),
                    "stdout": output,
                    "exit_code": exit_code,
                    }
                    
        self.crash_dump(self._output_dir, output)
        raise ValueError(f"Throughput command failed and exited with: {exit_code}")

    def cleanup(self):
        log.debug("no cleanup needed for wrk1 load generator")

    def wrk_has_rate(self):
        wrk = subprocess.Popen(['wrk', '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell = False)
        wrk.wait()
        output = wrk.communicate()[0].decode("utf-8")
        return '--rate' in output

    def parse_measurements(self, measurement):
        log.info("Parsing received measurements for throughput")
        return self.load_parser(measurement)['throughput']
