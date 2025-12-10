import json
import argparse
import logging as log
import time
import uuid
import os
import math
from enum import Enum
from datetime import datetime, timedelta
import re
import collections.abc
from argparse import ArgumentParser
import sys

#Stores map of supported p values
P_VALUES_MAP = {
    'p50': 50.0,
    'p75': 75.0,
    'p90': 90.0,
    'p99': 99.0,
    'p9999': 99.99,
    'p99999': 99.999,
    'p100': 100
}

class ServiceMode(Enum):
    JVM = 1
    NATIVE = 2

class LatencyMode(Enum):
    FIXED = 1
    BINARY_SEARCH = 2
    AIMD = 3

class Configuration:
    def __init__(self, benchmark_registry):
        self._benchmark_registry = benchmark_registry
        self._args = self.parse_arguments()
        self.set_bench_name()
        self.load_and_set_config()
        self.init_logger_and_create_output_dir()
        self.check_and_set_all()

    def describe(self):
        description = f"Benchmarking of {self._endpoint} with {self.mode._name_} mode\n"
        description += f"Redirecting output to: {self._output_folder}\n"

        description += self.startup.describe()
        description += self._warmup.describe()
        description += self._throughput.describe()
        description += self._latency.describe()

        total_runtime = self._warmup.get_total_runtime() + self._throughput.get_total_runtime() + self._latency.get_total_runtime()
        total_runtime_formatted = str(timedelta(seconds=total_runtime))

        end_time_formatted = datetime.now() + timedelta(0,total_runtime)
        description += f"Total runtime: {total_runtime_formatted}. Expected finish time {end_time_formatted}\n"

        return description

    def parse_arguments(self):
        """Returns an ArgumentParser object that parses arguments needed for the load testing of Barista benchmarks.
        """
        # Avoid using default values for any option that can be defined inside the config file
        # as the default value would take precedence over the value in the config file
        parser = ArgumentParser(prog="barista")
        # Positional arguments
        parser.add_argument("benchmark", choices=self.benchmark_registry.benchmark_names, help="Name of the benchmark")
        # General options
        parser.add_argument("-j", "--java-home", help="Path to the JVM distribution to be used. If not provided, the JAVA_HOME environment variable is used")
        parser.add_argument("-m", "--mode", choices=["jvm", "native"], help="Execution mode of the app")
        parser.add_argument("-c", "--config", default="default.barista.json", help="Path to the configuration JSON file to be used for load testing, can be either absolute or relative to the <bench-dir>/workloads directory. Defaults to 'default.barista.json'")
        parser.add_argument("-x", "--app-executable", help="Path to the application executable. If this is not set, the application executable is retrieved (built, in the case of native execution) from the benchmark directory")
        parser.add_argument("-e", "--endpoint", help="Endpoint of the application which will be loaded")
        parser.add_argument("-o", "--output", help="Path to the directory in which a timestamped directory will be created. Barista stores all its output in this timestamped directory. Defaults to the current working directory.")
        parser.add_argument("-t", "--threads", help="Number of threads to use during the warmup, throughput and latency load-testing phases. This option can be overwritten for each of the mentioned phases. During each phase, the number of threads is propagated to wrk/wrk2. The number of threads is also propagated to the Lua script that the wrk/wrk2 tool executes, enabling the writing of scripts that are aware of the number of threads executing them.")
        parser.add_argument("-k", "--connections", help="Connections to keep open during the warmup, throughput and latency load-testing phases. This option can be overwritten for each of the mentioned phases. During each phase, the number of connections is propagated to wrk/wrk2.")
        parser.add_argument("-s", "--lua-script", help="Lua script to be executed by wrk/wrk2 for general benchmarking purposes")
        parser.add_argument("--resource-usage-polling-interval", help="Time interval in seconds between two subsequent resource usage polls. Determines how often resource usage metrics, such as rss (Resident Set Size), vms (Virtual Memory Size), and CPU utilization, are collected. If set to 0 resource usage polling is disabled. Defaults to 0.02s (20ms)")
        parser.add_argument("--memory-refresh", action="store_true", help="Refresh the memory before running the application, ensuring cold system state. Flushes file system buffers, drops caches, and cycles swap space. Supported only on Linux. Requires sudo (root). Disabled by default.")
        parser.add_argument("--ignore-deps-bin", action="store_true", help="By default, Barista prepends its 'deps/bin' directory to PATH when executing subprocesses to facilitate access to its dependencies. By setting this option, the behaviour will be disabled.")
        parser.add_argument("--skip-prepare", action="store_true", help="Explicitly skip the prepare step of the benchmark, even if a prepare script is present in the benchmark directory")
        parser.add_argument("--skip-cleanup", action="store_true", help="Explicitly skip the cleanup step of the benchmark, even if a cleanup script is present in the benchmark directory")
        parser.add_argument("-d", "--debug", action="store_true", help="Show debug logs")
        # Prefix/propagate options
        parser.add_argument("-p", "--cmd-app-prefix", help="Command to be prefixed to the application command")
        parser.add_argument("--cmd-app-prefix-init-sleep", help="Sleep time, in seconds, for the initialization purposes of the command that is prefixed to the application command. The harness will sleep for this time duration and only then will it start attempting to detect the application process. Defaults to 0")
        parser.add_argument("--dummy-run-after-memory-refresh", action="store_true", help="Run a dummy prefix command after memory refresh to prevent side effects caused by the command prefix to be measured during benchmark execution. Disabled by default.")
        parser.add_argument("-v", "--vm-options", help="Options to be propagated to the virtual machine (JVM in jvm execution mode, native-image in native execution mode)")
        parser.add_argument("-a", "--app-args", help="Arguments to be propagated to the application")
        parser.add_argument("-b", "--native-image-build-options", help="Options to be propagated to the native-image build command (used only in native execution mode when no '--app-executable' option is provided)")
        # Startup options
        parser.add_argument("--startup-iteration-count", help="Number of startup iterations to execute. The data collected in the startup iterations is then aggregated. Defaults to 10")
        parser.add_argument("--startup-request-count", help="Number of requests to make and record the response time of, immediately after starting the application, in each startup iteration. Defaults to 10")
        parser.add_argument("--startup-timeout", help="Period of time without receiving a response from the app after which it is deemed unresponsive and the benchmark is stopped. If set to 0 the app will never be deemed unresponsive. Defaults to 60")
        parser.add_argument("--startup-cmd-app-prefix", help="Command to be prefixed to the application command, specifically just for the startup phase")
        parser.add_argument("--startup-cmd-app-prefix-init-sleep", help="Sleep time, in seconds, for the initialization purposes of the command that is prefixed to the application command specifically just for the startup phase. The harness will sleep for this time duration and only then will it start attempting to detect the application process. Defaults to 0")
        parser.add_argument("--startup-dummy-run-after-memory-refresh", action="store_true", help="Run a dummy startup prefix command after memory refresh to prevent side effects caused by the command prefix to be measured during startup benchmark execution. This option is specific to just the startup phase. Disabled by default.")
        # Warmup options
        parser.add_argument("--warmup-iteration-count", help="Number of iterations that should be performed before testing the application")
        parser.add_argument("--warmup-duration", help="Single iteration warmup time duration in seconds. How long should the application be stressed before testing")
        parser.add_argument("--warmup-threads", help="Number of threads to use for warmup, overrides the '--threads' option specifically for warmup iterations")
        parser.add_argument("--warmup-connections", help="Connections to keep open during warmup, overrides the '--connections' option specifically for warmup iterations")
        parser.add_argument("--warmup-lua-script", help="Lua script to be executed by wrk during warmup, overrides the '--lua-script' option specifically for warmup iterations")
        # Throughput options
        parser.add_argument("--throughput-iteration-count", help="Number of iterations that will be performed to measure throughput")
        parser.add_argument("--throughput-duration", help="Duration in seconds of a single iteration of throughput measurement")
        parser.add_argument("--throughput-threads", help="Number of threads to use for throughput measurements, overrides the '--threads' option specifically for throughput iterations")
        parser.add_argument("--throughput-connections", help="Connections to keep open during throughput measurements, overrides the '--connections' option specifically for throughput iterations")
        parser.add_argument("--throughput-lua-script", help="Lua script to be executed by wrk during throughput measurements, overrides the '--lua-script' option specifically for throughput iterations")
        # Latency options
        parser.add_argument("--latency-iteration-count", help="Number of iterations that will be performed to measure latency")
        parser.add_argument("--latency-duration", help="Time in seconds of how long should single iteration of latency measurment take")
        parser.add_argument("--latency-threads", help="Number of threads to use for latency measurements, overrides the '--threads' option specifically for latency iterations")
        parser.add_argument("--latency-connections", help="Connections to keep open during latency measurements, overrides the '--connections' option specifically for latency iterations")
        parser.add_argument("--latency-search-strategy", help="Strategy to be used when searching for the optimal throughput")
        parser.add_argument("--latency-rate", help="Constant throughput (in ops/sec) applied to measure latency")
        parser.add_argument("--latency-percentages", help="Fraction of throughput recorded in throughput measurements to be used in latency measurements")
        parser.add_argument("--latency-min-step-percent", help="Accuracy with which to perform the latency search")
        parser.add_argument("--latency-sla", help="Latency Service Level Agreement entry")
        parser.add_argument("--latency-lua-script", help="Lua script to be executed by wrk2 during latency measurements, overrides the '--lua-script' option specifically for latency iterations")

        if len(sys.argv) == 1:
            raise ValueError(f"benchmark is required, please choose from: [`{'`, `'.join(self.benchmark_registry.benchmark_names)}`]")

        args = parser.parse_args()
        return args

    def init_logger_and_create_output_dir(self):
        if self._args.output is not None:
            output_folder = self._args.output
        else:
            output_folder = self._config.get('output_dir', './')
        exists = os.path.exists(output_folder)
        if not exists:
            os.makedirs(output_folder, exist_ok=True)
        t = time.localtime()
        # reused for subsequent file creation as folder name
        
        current_time = time.strftime("%Y-%m-%d_%H-%M-%S", t) + "-bench-" + str(uuid.uuid4())[:6]
        self._output_folder = os.path.join(output_folder, current_time)
        os.mkdir(self._output_folder)

        log_file_path = os.path.abspath(os.path.join(self._output_folder, "barista.log"))
        log.basicConfig(
            format = "%(asctime)s [%(levelname)s] %(message)s",
            handlers = [
                log.FileHandler(log_file_path),
                log.StreamHandler()
            ],
            level = "DEBUG" if self._args.debug else "INFO"
        )

    def set_bench_name(self):
        self._bench_name = self._args.benchmark

    def benchmark_directory(self):
        return self.benchmark_registry.get_benchmark_dir(self._bench_name)

    def load_and_set_config(self):
        if os.path.isabs(self._args.config):
            self._config_path = self._args.config
        else:
            self._config_path = os.path.join(self.benchmark_directory(), "workloads", self._args.config)
        if not os.path.isfile(self._config_path):
            raise FileNotFoundError(f"Workload configuration file not found at \"{self._config_path}\"")
        with open(self._config_path, "r") as jsonfile:
            try:
                config = json.load(jsonfile)
            except json.decoder.JSONDecodeError as ex:
                raise SyntaxError(f"Invalid json file. Please ensure the json file at {self._config_path} is valid") from ex
            self._config = config

    def check_and_set_all(self):
        self.check_and_set_app_arg()
        self.check_and_set_startup_arguments()
        self.check_and_set_warmup_arguments()
        self.check_and_set_throughput_arguments()
        self.check_and_set_latency_arguments()
        self._execution_context_file_path = os.path.join(self.benchmark_directory(), "barista-execution-context")

    def check_and_set_app_arg(self):
        if self._args.java_home is not None:
            self._java_home = self._args.java_home
        else:
            self._java_home = os.getenv("JAVA_HOME")

        if self._args.app_executable is not None:
            # CLI overwrites config file
            self._app_executable = self._args.app_executable
        elif 'app_executable' in self._config:
            self._app_executable = self._config['app_executable']
        else:
            self._app_executable = None
        if self._app_executable is not None and not os.path.isabs(self._app_executable):
            self._app_executable = os.path.join(os.path.dirname(__file__), self._app_executable)
        if self._app_executable is not None and not os.path.isfile(self._app_executable):
            self._app_executable = None

        if self._args.cmd_app_prefix is not None:
            # CLI overwrites config file
            self._cmd_app_prefix = self._args.cmd_app_prefix.split()
        elif 'cmd_app_prefix' in self._config:
            self._cmd_app_prefix  = self._config['cmd_app_prefix']
        else:
            self._cmd_app_prefix = None

        if self._args.cmd_app_prefix_init_sleep is not None:
            prefix_init_sleep = int(self._args.cmd_app_prefix_init_sleep)
        elif 'cmd_app_prefix_init_sleep' in self._config:
            prefix_init_sleep = int(self._config['cmd_app_prefix_init_sleep'])
        else:
            # Defaults to 0s
            prefix_init_sleep = 0
        self._cmd_app_prefix_init_sleep = prefix_init_sleep

        self._dummy_run_after_memory_refresh = self._args.dummy_run_after_memory_refresh

        if self._args.native_image_build_options is not None:
            # CLI overwrites config file
            self._native_image_build_options = self.ensure_is_array(self._args.native_image_build_options.split())
        elif 'native_image_build_options' in self._config:
            self._native_image_build_options  = self.ensure_is_array(self._config['native_image_build_options'])
        else:
            self._native_image_build_options = []

        if self._args.mode is not None:
            # CLI overwrites config file
            mode = self._args.mode.upper()
        elif 'mode' in self._config:
            mode  = self._config['mode'].upper()
        else:
            mode = "JVM"
            log.debug(f"No execution mode set. Defaulting to '{mode}' execution mode")
        self._mode = ServiceMode[mode]

        if self._args.vm_options is not None:
            # CLI overwrites config file
            self._vm_options = self._args.vm_options.split()
        elif 'vm_options' in self._config:
            self._vm_options = self._config['vm_options']
        else:
            self._vm_options = []

        if self._args.app_args is not None:
            # CLI overwrites config file
            self._app_args = self._args.app_args.split()
        elif 'app_args' in self._config:
            self._app_args = self._config['app_args']
        else:
            self._app_args = []

        if self._args.endpoint is not None:
            # CLI overwrites config file
            self._endpoint = self._args.endpoint
        elif 'endpoint' in self._config:
            self._endpoint  = self._config['endpoint']
        else:
            raise ValueError(f"Configuration or command line argument must have key 'endpoint' for target application")

        url_pattern = "^((?:[^\/]*:\/\/)?)([^:\/]+)((?::\d+)?)((?:\/.*)?)$"
        url_match = re.search(url_pattern, self._endpoint)
        if not url_match:
            raise ValueError(f"Unparsable endpoint value: {self._endpoint}! Expected: [<protocol>://]<domain>[:<port>][/path]")
        self._endpoint_protocol = url_match.group(1)[:-3] if url_match.group(1) else "http"
        supported_protocols = ["http", "https"]
        if not self._endpoint_protocol in supported_protocols:
            raise ValueError(f"Unsupported internet protocol '{self._endpoint_protocol}' used in endpoint '{self._endpoint}'. Please use one of the supported protocols: [`{'`, `'.join(supported_protocols)}`]")
        self._endpoint_domain = url_match.group(2)
        if url_match.group(3):
            self._endpoint_port = url_match.group(3)[1:]
        elif self._endpoint_protocol == "http":
            self._endpoint_port = 80
        else:
            self._endpoint_port = 443
        self._endpoint_path = url_match.group(4) if url_match.group(4) else "/"

        if self._args.resource_usage_polling_interval is not None:
            # CLI overwrites config file
            polling_interval = float(self._args.resource_usage_polling_interval)
        elif 'resource_usage_polling_interval' in self._config:
            polling_interval = float(self._config['resource_usage_polling_interval'])
        else:
            polling_interval = 0.02 # 20 ms
            log.debug(f"No resource usage polling interval set. Defaulting to {polling_interval} seconds ({polling_interval * 1000}ms)")
        self._resource_usage_polling_interval = polling_interval

        env = os.environ.copy()
        ignore_deps_bin = self._args.ignore_deps_bin
        if not ignore_deps_bin:
            path = env.get("PATH", "")
            deps_bin = os.path.join(os.path.dirname(__file__), "deps", "bin")
            env["PATH"] = f"{deps_bin}:{path}" if path else deps_bin
        self._env = env

        self._memory_refresh = self._args.memory_refresh
        self._skip_prepare = self._args.skip_prepare
        self._skip_cleanup = self._args.skip_cleanup

    def ensure_is_array(self, x):
        return x if isinstance(x, collections.abc.Sequence) and not isinstance(x, str) else [x]

    def ensure_script_file_exists(self, paths):
        script_paths = self.ensure_is_array(paths)
        for idx, script_path in enumerate(script_paths):
            # Check if the path is absolute
            script_paths[idx] = os.path.abspath(script_path)
            if os.path.isfile(script_paths[idx]):
                continue
            # Check if the path is relative to the config file
            script_paths[idx] = os.path.abspath(os.path.join(os.path.dirname(self._config_path), script_path))
            if os.path.isfile(script_paths[idx]):
                continue
            raise FileNotFoundError(f"Specified lua script '{script_path}' not found. Please ensure the supplied path is either absolute or relative to the configuration json file '{self._config_path}'")
        return script_paths

    def check_and_set_startup_arguments(self):
        startup_config = self._config["load_testing"]["startup"] if "startup" in self._config["load_testing"] else {}

        if self._args.startup_iteration_count is not None:
            iteration_count = int(self._args.startup_iteration_count)
        elif "iterations" in startup_config:
            iteration_count = int(startup_config["iterations"])
        else:
            iteration_count = 10
            log.debug(f"No startup iteration count set. Defaulting to {iteration_count} iterations")

        if self._args.startup_request_count is not None:
            request_count = int(self._args.startup_request_count)
        elif "requests" in startup_config:
            request_count = int(startup_config["requests"])
        else:
            request_count = 10
            log.debug(f"No startup request count set. Defaulting to {request_count} requests")
        if iteration_count > 0 and request_count <= 0:
            raise ValueError("'startup' must have either a positive value for 'requests' or be disabled by setting 'iterations' to 0")

        if self._args.startup_timeout is not None:
            timeout = int(self._args.startup_timeout)
        elif "timeout" in startup_config:
            timeout = int(startup_config["timeout"])
        else:
            timeout = 60
            log.debug(f"No startup timeout set. Defaulting to {timeout} seconds")

        if self._args.startup_cmd_app_prefix is not None:
            cmd_app_prefix = self._args.startup_cmd_app_prefix.split()
        elif "cmd_app_prefix" in startup_config:
            cmd_app_prefix = startup_config["cmd_app_prefix"]
        else:
            cmd_app_prefix = self._cmd_app_prefix

        if self._args.startup_cmd_app_prefix_init_sleep is not None:
            prefix_init_sleep = int(self._args.startup_cmd_app_prefix_init_sleep)
        elif 'cmd_app_prefix_init_sleep' in startup_config:
            prefix_init_sleep = int(startup_config['cmd_app_prefix_init_sleep'])
        else:
            # Defaults to 0s
            prefix_init_sleep = 0
        
        dummy_run_after_memory_refresh = self._args.startup_dummy_run_after_memory_refresh

        self._startup = self.StartupConfig(iteration_count, request_count, timeout, cmd_app_prefix, prefix_init_sleep, dummy_run_after_memory_refresh)

    def check_and_set_warmup_arguments(self):
        script = None
        iteration_duration = 0
        iteration_count = 0
        
        warmup_config = self._config['load_testing']['warmup']
        if self._args.warmup_duration is not None:
            iteration_duration = int(self._args.warmup_duration)
        elif 'iteration_time_seconds' in warmup_config:
            iteration_duration = warmup_config['iteration_time_seconds']
        else:
            raise ValueError("'warmup' must have 'iteration_time_seconds' option")

        if self._args.warmup_iteration_count is not None:
            iteration_count = int(self._args.warmup_iteration_count)
        elif 'iterations' in warmup_config:
            iteration_count = warmup_config['iterations']
        else :
            raise ValueError("'warmup' must have 'iterations' option")

        if self._args.warmup_threads is not None:
            threads = self._args.warmup_threads
        elif self._args.threads is not None:
            threads = self._args.threads
        elif 'threads' in self._config['load_testing']['warmup']:
            threads = self._config['load_testing']['warmup']['threads']
        elif 'threads' in self._config['load_testing']:
            threads = self._config['load_testing']['threads']
        else:
            threads = 1
            log.debug(f"No warmup threads set. Defaulting to {threads} threads")

        if self._args.warmup_connections is not None:
            connections = self._args.warmup_connections
        elif self._args.connections is not None:
            connections = self._args.connections
        elif 'connections' in self._config['load_testing']['warmup']:
            connections = self._config['load_testing']['warmup']['connections']
        elif 'connections' in self._config['load_testing']:
            connections = self._config['load_testing']['connections']
        else:
            connections = 1
            log.debug(f"No warmup connections set. Defaulting to {connections} connections")

        if self._args.warmup_lua_script is not None:
            script = self.ensure_script_file_exists(self._args.warmup_lua_script)
        elif self._args.lua_script is not None:
            script = self.ensure_script_file_exists(self._args.lua_script)
        elif 'lua_script' in self._config['load_testing']['warmup']:
            script = self.ensure_script_file_exists(self._config['load_testing']['warmup']['lua_script'])
        elif 'lua_script' in self._config['load_testing']:
            script = self.ensure_script_file_exists(self._config['load_testing']['lua_script'])

        self._warmup = self.WarmupConfig(iteration_duration, iteration_count, script, threads, connections)

    def check_and_set_throughput_arguments(self):
        script = None
        iteration_duration = 0
        iteration_count = 0

        throughput_config = self._config['load_testing']['throughput']
        if self._args.throughput_duration is not None:
            iteration_duration = int(self._args.throughput_duration)
        elif 'iteration_time_seconds' in throughput_config:
            iteration_duration = throughput_config['iteration_time_seconds']
        else:
            log.warning(f"No throughput duration set. Defaulting to {self._warmup.iteration_duration}s")
        
        if self._args.throughput_iteration_count is not None:
            iteration_count = int(self._args.throughput_iteration_count)
        elif 'iterations' in throughput_config:
            iteration_count = throughput_config['iterations']
        else:
            log.warning(f"No throughput iteration count set. Defaulting to {self._warmup.iteration_count}")

        if self._args.throughput_threads is not None:
            threads = self._args.throughput_threads
        elif self._args.threads is not None:
            threads = self._args.threads
        elif 'threads' in throughput_config:
            threads = throughput_config['threads']
        elif 'threads' in self._config['load_testing']:
            threads = self._config['load_testing']['threads']
        else:
            threads = 1
            log.debug(f"No throughput threads set. Defaulting to {threads} threads")

        if self._args.throughput_connections is not None:
            connections = self._args.throughput_connections
        elif self._args.connections is not None:
            connections = self._args.connections
        elif 'connections' in throughput_config:
            connections = throughput_config['connections']
        elif 'connections' in self._config['load_testing']:
            connections = self._config['load_testing']['connections']
        else:
            connections = 1
            log.debug(f"No throughput connections set. Defaulting to {connections} connections")

        if self._args.throughput_lua_script is not None:
            script = self.ensure_script_file_exists(self._args.throughput_lua_script)
        elif self._args.lua_script is not None:
            script = self.ensure_script_file_exists(self._args.lua_script)
        elif 'lua_script' in throughput_config:
            script = self.ensure_script_file_exists(throughput_config['lua_script'])
        elif 'lua_script' in self._config['load_testing']:
            script = self.ensure_script_file_exists(self._config['load_testing']['lua_script'])
        self._throughput = self.ThroughputConfig(iteration_duration, iteration_count, script, threads, connections)

    def check_and_set_latency_arguments(self):
        log.debug("Checking Latency management options")

        script = None
        iteration_duration = 0
        iteration_count = 0
        strategy = None
        percentages = None
        rates=None
        base_step = None
        defined_slas = None
        sla_requirement= None

        latency_config = self._config['load_testing']['latency_measurement']
        if self._args.latency_duration is not None:
            iteration_duration = int(self._args.latency_duration)
        elif 'iteration_time_seconds' in latency_config:
            iteration_duration = latency_config['iteration_time_seconds']
        else:
            raise ValueError(f"'latency_measurement' must have 'iteration_time_seconds' option")

        if self._args.latency_iteration_count is not None:
            iteration_count = int(self._args.latency_iteration_count)
        elif 'iterations' in latency_config:
            iteration_count = latency_config['iterations']
        else:
            raise ValueError(f"'latency_measurement' must have 'iterations' option")

        if self._args.latency_threads is not None:
            threads = self._args.latency_threads
        elif self._args.threads is not None:
            threads = self._args.threads
        elif 'threads' in latency_config:
            threads = latency_config['threads']
        elif 'threads' in self._config['load_testing']:
            threads = self._config['load_testing']['threads']
        else:
            threads = 1
            log.debug(f"No latency threads set. Defaulting to {threads} threads")

        if self._args.latency_connections is not None:
            connections = self._args.latency_connections
        elif self._args.connections is not None:
            connections = self._args.connections
        elif 'connections' in latency_config:
            connections = latency_config['connections']
        elif 'connections' in self._config['load_testing']:
            connections = self._config['load_testing']['connections']
        else:
            connections = 1
            log.debug(f"No latency connections set. Defaulting to {connections} connections")

        # Set lua scripts
        if self._args.latency_lua_script is not None:
            script = self.ensure_script_file_exists(self._args.latency_lua_script)
        elif self._args.lua_script is not None:
            script = self.ensure_script_file_exists(self._args.lua_script)
        elif 'lua_script' in self._config['load_testing']['latency_measurement']:
            script = self.ensure_script_file_exists(self._config['load_testing']['latency_measurement']['lua_script'])
        elif 'lua_script' in self._config['load_testing']:
            script = self.ensure_script_file_exists(self._config['load_testing']['lua_script'])

        # Set search strategy
        if self._args.latency_search_strategy is not None:
            search_strategy_name = self._args.latency_search_strategy
        elif 'search_strategy' in latency_config:
            search_strategy_name = latency_config['search_strategy']
        else:
            raise ValueError("Barista load-tester must have a search strategy for latency measurements, please provide option '--latency-search-strategy' or update the config JSON to include a latency search strategy")
        if search_strategy_name == 'FIXED':
            strategy = LatencyMode.FIXED
        elif search_strategy_name == 'BINARY_SEARCH':
            strategy = LatencyMode.BINARY_SEARCH
        elif search_strategy_name == 'AIMD':
            strategy = LatencyMode.AIMD
        else:
            raise ValueError(f"Unrecognized value {search_strategy_name} for latency search strategy. Supported modes: {[enum.name for enum in LatencyMode]}")

        # Set strategy specific args
        if strategy == LatencyMode.FIXED:
            if self._args.latency_rate is not None:
                rates = self.ensure_is_array(self._args.latency_rate)
            elif 'rates' in latency_config:
                rates = self.ensure_is_array(latency_config['rates'])
            if self._args.latency_percentages is not None:
                percentages = self.ensure_is_array(self._args.latency_percentages)
            elif 'percentages' in latency_config:
                percentages = self.ensure_is_array(latency_config['percentages'])
            if percentages is not None and self._throughput.iteration_count <= 0:
                raise ValueError(f"'percentages' field provided for latency measurements, must have at least 1 preceding 'throughput' iteration({self.throughput.iteration_count}<=0)")
            if percentages is None and rates is None and iteration_count>0:
                raise ValueError("'FIXED' strategy must have at least 'rates' or 'percentages' field in 'latency_measurement'")
        if strategy == LatencyMode.BINARY_SEARCH or strategy == LatencyMode.AIMD:
            if self._args.latency_min_step_percent is not None:
                base_step = int(self._args.latency_min_step_percent)
            elif 'min_step_percent' in latency_config:
                base_step = latency_config['min_step_percent']
            else:
                raise ValueError(f"'{strategy.name}' latency search strategy must have at least 'min_step_percent' defined")
            if self._throughput.iteration_count <= 0:
                raise ValueError(f"'{strategy.name}' latency search strategy must have at least 1 preceding 'throughput' iteration({self.throughput.iteration_count}<=0)")

        if self._args.latency_sla is not None:
            defined_slas = self._args.latency_sla
        elif 'SLA' in latency_config:
            defined_slas = latency_config['SLA']
        if defined_slas is not None:
            supported_values = ','.join(P_VALUES_MAP.keys())
            p_requirements = dict()
            for p_value_pair in defined_slas:
                p_string = p_value_pair[0]
                latency_value = p_value_pair[1]
                if p_string in P_VALUES_MAP:
                    p_requirements[P_VALUES_MAP[p_string]] = latency_value
                else:
                    raise ValueError(f"The p value {p_string} is not supported. Supported p values are: <{supported_values}>")

            sla_requirement = p_requirements

        if sla_requirement is None and (strategy == LatencyMode.BINARY_SEARCH or strategy == LatencyMode.AIMD):
            raise ValueError(f"SLA field must be present with {strategy.name} strategy")

        self._latency = self.LatencyConfig(iteration_duration, iteration_count, strategy, percentages, rates, base_step, sla_requirement, script, threads, connections)

    def read_from_execution_context_file(self, field_name, default=None):
        # tomllib was included in python standard library with version 3.11
        try:
            import tomllib
            with open(self.execution_context_file_path, mode="rb") as execution_context:
                return tomllib.load(execution_context).get(field_name, default)
        except ImportError:
            pass

        # fallback to 'toml' library if tomllib is not present
        try:
            import toml
            with open(self.execution_context_file_path, mode="rt") as execution_context:
                return toml.loads(execution_context.read()).get(field_name, default)
        except ImportError:
            log.error(f"Could not read the {field_name} field from the execution context toml file because there is no toml parser installed. Use python3.11+ or install `toml` with pip.")
            raise

    def update_after_benchmark_prepare(self):
        if not os.path.isfile(self.execution_context_file_path):
            return

        app_args_from_execution_context = self.read_from_execution_context_file("app-args", "").split()
        log.debug(f"Expanding configuration with app arguments from the execution context file: {app_args_from_execution_context}")
        self._app_args = app_args_from_execution_context + self._app_args

        vm_options_from_execution_context = self.read_from_execution_context_file("vm-options", "").split()
        log.debug(f"Expanding configuration with VM options from the execution context file: {vm_options_from_execution_context}")
        self._vm_options = vm_options_from_execution_context + self._vm_options

    @property
    def benchmark_registry(self):
        return self._benchmark_registry

    @property
    def output_folder(self):
        return self._output_folder

    @property
    def bench_name(self):
        return self._bench_name

    @property
    def java_home(self):
        return self._java_home

    @property
    def app_executable(self):
        return self._app_executable

    @app_executable.setter
    def app_executable(self, value):
        self._app_executable = value

    @property
    def cmd_app_prefix(self):
        return self._cmd_app_prefix

    @property
    def cmd_app_prefix_init_sleep(self):
        return self._cmd_app_prefix_init_sleep
    
    @property
    def dummy_run_after_memory_refresh(self):
        return self._dummy_run_after_memory_refresh

    @property
    def mode(self):
        return self._mode

    @property
    def vm_options(self):
        return self._vm_options

    @property
    def app_args(self):
        return self._app_args

    @property
    def build_options(self):
        return self._native_image_build_options

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def endpoint_protocol(self):
        return self._endpoint_protocol

    @property
    def endpoint_domain(self):
        return self._endpoint_domain

    @property
    def endpoint_port(self):
        return self._endpoint_port

    @property
    def endpoint_path(self):
        return self._endpoint_path

    @property
    def resource_usage_polling_interval(self):
        return self._resource_usage_polling_interval

    @property
    def env(self):
        return self._env

    @property
    def memory_refresh(self):
        return self._memory_refresh

    @property
    def skip_prepare(self):
        return self._skip_prepare

    @property
    def skip_cleanup(self):
        return self._skip_cleanup

    @property
    def startup(self):
        return self._startup

    @property
    def warmup(self):
        return self._warmup

    @property
    def throughput(self):
        return self._throughput

    @property
    def latency(self):
        return self._latency

    @property
    def execution_context_file_path(self):
        return self._execution_context_file_path

    class StartupConfig:
        def __init__(self, iteration_count, request_count, timeout, cmd_app_prefix, cmd_app_prefix_init_sleep, dummy_run_after_memory_refresh):
            self._iteration_count = iteration_count
            self._request_count = request_count
            self._timeout = timeout
            self._cmd_app_prefix = cmd_app_prefix
            self._cmd_app_prefix_init_sleep = cmd_app_prefix_init_sleep
            self._dummy_run_after_memory_refresh = dummy_run_after_memory_refresh

        def describe(self):
            return f"\t - Startup: Repeat {self.iteration_count} iterations: recording first {self.request_count} requests, timeout after {self.timeout} seconds of no response\n"

        @property
        def iteration_count(self):
            return self._iteration_count

        @property
        def request_count(self):
            return self._request_count

        @property
        def timeout(self):
            return self._timeout

        @property
        def cmd_app_prefix(self):
            return self._cmd_app_prefix

        @property
        def cmd_app_prefix_init_sleep(self):
            return self._cmd_app_prefix_init_sleep
    
        @property
        def dummy_run_after_memory_refresh(self):
            return self._dummy_run_after_memory_refresh

    class WarmupConfig:
        def __init__(self, it_duration, it_count, script, threads, connections):
            # init defaults
            self._iteration_duration = it_duration
            self._iteration_count = it_count
            self._threads = threads
            self._connections = connections
            self._script = script

        def describe(self):
            description = f"\t - Warmup: {self.iteration_count} iterations of {self.iteration_duration} seconds with {self.threads} threads and {self.connections} connections"
            if self.script is not None:
                description += f" (lua script: {self.script})"
            description += "\n"
            return description

        def get_total_runtime(self):
            return self.iteration_count * self.iteration_duration

        @property
        def iteration_duration(self):
            return self._iteration_duration

        @property
        def iteration_count(self):
            return self._iteration_count

        @property
        def threads(self):
            return self._threads

        @property
        def connections(self):
            return self._connections

        @property
        def script(self):
            return self._script

    class LatencyConfig:
        def __init__(self, it_duration, it_count, strategy, percentages, rates ,base_step, sla_requirement, script, threads, connections):
            # init defaults
            self._iteration_duration = it_duration
            self._iteration_count = it_count
            self._threads = threads
            self._connections = connections
            self._script = script
            self._search_strategy = strategy
            self._base_step = base_step
            self._bounds = 0.03
            self._percentages = percentages
            self._rates = rates
            self._sla_requirement = sla_requirement

        def describe(self):
            if self.search_strategy == LatencyMode.FIXED:
                description = f"\t - Latency: {self.iteration_count} iterations of {self.iteration_duration} seconds with {self.threads} threads and {self.connections} connections at "
                if self.rates is not None:
                    description += f"{str(self.rates)} reqs/s "
                    if self.percentages is not None:
                        description += "and "
                if self.percentages is not None:
                    description += f"max average throughput percentages: {self.percentages}"
            else:
                description = f"\t - Latency: will determine optimal rate that meets the SLA : {self.sla_requirement} with {self.search_strategy.name} strategy.\n"
                description += f" \t\t And then will perform {self.iteration_count} iterations of {self.iteration_duration} seconds at the determined rate"

            if self.script is not None:
                description += f"(lua script: {self.script})"

            description += "\n"
            return description

        def get_aimd_runtime(self):
            return 3 * (int(math.log(1 / self.base_step, 2)) + 1) * 30

        def get_binary_search_runtime(self):
            return int(math.log(1/self.base_step, 2)) * 30

        def get_total_runtime(self):
            if self.search_strategy == LatencyMode.FIXED:
                p_it = 0
                r_it = 0
                if self.percentages is not None:
                    p_it = len(self.percentages)
                if self.rates is not None:
                    r_it = len(self.rates)
                return self.iteration_count * self.iteration_duration * (r_it + p_it)
            elif self.search_strategy == LatencyMode.BINARY_SEARCH:
                return self.iteration_count * self.iteration_duration + self.get_binary_search_runtime()
            elif self.search_strategy == LatencyMode.AIMD:
                return self.iteration_count * self.iteration_duration + self.get_aimd_runtime()
            else:
                raise ValueError("Latency Configuration must have search strategy.")

        @property
        def iteration_duration(self):
            return self._iteration_duration

        @property
        def iteration_count(self):
            return self._iteration_count

        @property
        def threads(self):
            return self._threads

        @property
        def connections(self):
            return self._connections

        @property
        def script(self):
            return self._script

        @property
        def base_step(self):
            return self._base_step

        @property
        def bounds(self):
            return self._bounds

        @property
        def percentages(self):
            return self._percentages

        @property
        def rates(self):
            return self._rates

        @property
        def search_strategy(self):
            return self._search_strategy

        @property
        def sla_requirement(self):
            return self._sla_requirement

    class ThroughputConfig:
        def __init__(self, it_duration, it_count, script, threads, connections):
            # init defaults
            self._iteration_count = it_count
            self._iteration_duration = it_duration
            self._threads = threads
            self._connections = connections
            self._script = script

        def describe(self):
            description = f"\t - Throughput: {self.iteration_count} iterations of {self.iteration_duration} seconds with {self.threads} threads and {self.connections} connections"
            if self.script is not None:
                description +=  f" (lua script: {self.script})"
            description += "\n"

            return description

        def get_total_runtime(self):
            return self.iteration_count + self.iteration_duration

        @property
        def iteration_count(self):
            return self._iteration_count

        @property
        def iteration_duration(self):
            return self._iteration_duration

        @property
        def threads(self):
            return self._threads

        @property
        def connections(self):
            return self._connections

        @property
        def script(self):
            return self._script