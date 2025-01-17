from app_manager import AppManager
import logging as log
import time
from http.client import HTTPConnection, HTTPSConnection
import math
from results import compile_p_values
from app_manager import AppProcessFinishedUnexpectedly

class StartupManager:
    """Manages the startup phase of the benchmark.

    Performs --startup-iteration-count iterations of the startup phase. Each phase is composed
    of three steps:
      1. Start the application process. Use --startup-cmd-app-prefix to set different tracker
         or resource constraint tool.
      2. Send --startup-request-count requests sequentially using `http.client.HTTPConnection`.
      3. Kill the application process.
    Once all the iterations are done, the median is calculated for each request and the resulting
    array is reported:
        [M1, M2, ..., Mx]
    Where Mi is the median of the i-th request after app cold start across all the iterations.

    The application is started one last time, this time with the non-startup-specific prefix
    specified with --cmd-app-prefix. This instance of the application will be used for all of
    the other load-testing phases (warmup, throughput, latency). The startup requests are also
    once more sent, but the data is not recorded anywhere. This was done in order to avoid
    starting the `wrk` or `wrk2` tool before the application process is responsive - `wrk` and
    `wrk2` would crash if they were started before the application finishes its startup. This
    instance of the application is not killed by the `StartupManager`.
    """
    def __init__(self, config):
        self._config = config
        self._app_manager = AppManager(config)
        self._iterations = []
        self._startup_data = []

    def run(self):
        """Runs the startup phase of the benchmark process."""
        for iteration_idx in range(self.config.startup.iteration_count):
            log.info(f"Running startup phase iteration #{iteration_idx + 1}")
            self.app_manager.start_app(self.config.startup.cmd_app_prefix, True)
            iteration_data = self._run_single_startup_iteration()
            self.kill_app()
            self._iterations.append(iteration_data)
        self._aggregate_iteration_data()

        self.app_manager.start_app(self.config.cmd_app_prefix)
        app_process = self.app_manager.app_process
        log.info(f"Detected app process (pid={app_process.pid}) with command-line:\n{' '.join(app_process.cmdline())}")
        self._run_single_startup_iteration()

        return self._startup_data

    def kill_app(self):
        self.app_manager.kill_app()

    def _run_single_startup_iteration(self):
        if self.config.startup.request_count <= 0:
            raise ValueError(f"Invalid request count for startup phase. Got '{self.config.startup.request_count}' but expected a positive integer!")

        iteration_data = []
        log.info(f"Running startup measurements: sending {self.config.startup.request_count} GET request(s) to {self.config.endpoint_protocol}://{self.config.endpoint_domain}:{self.config.endpoint_port}{self.config.endpoint_path}")
        for request_idx in range(self.config.startup.request_count):
            if request_idx == 0:
                ts_before_request = self.app_manager.start_ts
            else:
                ts_before_request = time.perf_counter()
            self._request_until_response(self.config.startup.timeout)
            response_time = (time.perf_counter() - ts_before_request) * 1000
            log.info(f"Received response #{request_idx + 1} in {response_time:6.2f} ms")
            iteration_data.append(response_time)
        return iteration_data

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
                    return_code = self.app_manager.root_process.poll()
                    if return_code is not None:
                        raise AppProcessFinishedUnexpectedly(f"Root process exited unexpectedly with return code {return_code}!")
                if timeout != 0 and ts_current - ts_start >= timeout:
                    raise TimeoutError(f"App '{self.config.bench_name}' unresponsive! Could not get a response after trying for {timeout} seconds!")
                time.sleep(0.001)

    def _aggregate_iteration_data(self):
        if not self._iterations:
            self._startup_data = []
            return

        self._startup_data = [{
            "response_time": self._nth_request_median(idx),
            "iteration": idx
        } for idx in range(self.config.startup.request_count)]

    def _nth_request_median(self, idx):
        return compile_p_values([x[idx] for x in self._iterations], [50])["p50.0"]

    @property
    def config(self):
        return self._config

    @property
    def app_manager(self):
        return self._app_manager
