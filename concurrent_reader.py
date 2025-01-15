from threading  import Thread
import process_info
import time
import logging as log
import re

def extract_default_microservice_times(output):
    """
    Given an output of a program returns a tuple of framework time and process time
    """
    framework_group_pattern = fr"(?P<framework>\d+(?:[\.,]\d+)?)"
    framework_startup = {
        "spring" : (fr"Started [^ ]+ in {framework_group_pattern} seconds \(process running for (?P<process>\d*[.,]?\d*)\)$", 1000),
        "quarkus" : (fr"started in (?:\x1b\[38;2;221;221;221m)?{framework_group_pattern}(?:\x1b\[39m)?s\.", 1000),
        "micronaut" : (fr"^.*\[main\].*INFO.*io.micronaut.runtime.Micronaut.*- Startup completed in {framework_group_pattern}ms.", 1),
        "vanilla" : (fr"Basic Hello-World HttpServer started after {framework_group_pattern}ms!", 1),
        "vertx" : (fr"Server listening on http://localhost:\d+/ after {framework_group_pattern}ms!", 1),
        "helidon": (fr"Started all channels in \d* milliseconds. {framework_group_pattern} milliseconds since JVM startup.", 1),
    }

    framework_startup_result = {}
    for framework, (framework_regex, startup_unit) in framework_startup.items():
        matches = re.search(framework_regex, output, re.MULTILINE)
        if matches is not None:
            framework_startup_result['framework-startup'] =  float(matches.group('framework')) * startup_unit
        if matches is not None and matches.groupdict().get('process'):
            framework_startup_result['process-startup'] = float(matches.group('process')) * startup_unit
    if len(framework_startup_result) == 0:
        return {}
    startup_time = framework_startup_result['framework-startup']
    log.info(f'Extracted framework startup time of {startup_time} ms')
    return framework_startup_result

class ConcurrentReader(Thread):
    """
    Concurrent Reader extends Thread from threading.
    Used for starting a thread that stores and prints stdout of the application being benchmarked.
    """

    def __init__(self, root_process, app_process, polling_interval):
        super(ConcurrentReader,self).__init__(target = self.enqueue_output, args = (root_process.stdout,))
        self._root_process = root_process
        self._app_process = app_process
        self._polling_interval = polling_interval
        self.daemon = True
        self._output = ""
        self._resources = []
        self._startup_times = {}
        self._resource_reader_thread = Thread(target=self.measure_proc_stats)
        

    def enqueue_output(self, out):
        for line in iter(out.readline, b''):
            try:
                line = line.decode()
                print(line)
                self._output += line
                if not self._startup_times:
                    self._startup_times = extract_default_microservice_times(line)
            except UnicodeError:
                log.debug("Encountered a line that could not be decoded on the stdout. It could be binary data. Ignoring it.")
        out.close()

    def start(self):
        self._resource_reader_thread.start()
        super().start()
        
    def measure_proc_stats(self):
        if self._polling_interval <= 0:
            log.info(f"Resource usage polling disabled by setting the interval to {self._polling_interval}")
            return

        log.info(f"Monitoring memory and CPU usage of process {self._app_process.pid} every {self._polling_interval * 1000}ms")
        try:
            while self._root_process.poll() is None:
                memory_info = self._app_process.memory_info()
                rss = memory_info.rss
                vms = memory_info.vms
                # Interval is blocking therefore no need for sleep
                cpu = self._app_process.cpu_percent(interval=self._polling_interval)
                self._resources.append((time.time() * 1000, rss, vms, cpu))
        except FileNotFoundError:
            # Process finished between `poll` call and `cpu_percent` call
            pass

    @property
    def output(self):
        return self._output

    @property
    def resources(self):
       return self._resources

    def join(self):
        self._resource_reader_thread.join()
        super().join()

    @property
    def startup_times(self):
        return self._startup_times