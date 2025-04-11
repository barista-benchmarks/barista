from configuration import ServiceMode
import logging as log
import subprocess
import process_info
import time

class AppManager:
    """Manages the starting and stopping of the app process.

    Exposes two methods that are of interest:
    * start_app
        The user should invoke the `start_app` method when they want the
        application to start operating. This method will instantiate a
        subprocess that runs the application JAR or executable - depending on
        the execution mode set in the configuration.
    * kill_app
        The user should invoke the `kill_app` method once they no longer
        require the application to be running. An invocation to `start_app`
        should always be matched with an invocation to `kill_app`, otherwise
        the process will remain running until terminated manually. Once the
        `kill_app` method has been invoked, it is safe to invoke the
        `start_app` method of the same AppManager instance in order to start
        another instance of the application.

    A few properties that could be of interest are also made accessible:
    * config
        Configuration specifying the desired parameters of the benchmark as a
        whole, containing parameters of running the application process.
    * root_process
        A subprocess.Popen object representing the root process started in the
        `start_app` method. Can represent the app process itself, but can also
        represent any tool that is invoked by the `cmd_app_prefix` parameter
        passed to the `start_app` method.
    * app_process
        An instance of psutil_replacement_linux.Process (or psutil.Process if
        not on linux) representing the application process itself. Can be used
        to retrieve resource usage information of the app.
    * start_ts
        Timestamp taken immediately before starting the application process.
    """
    def __init__(self, config):
        self._config = config
        self._root_process = None
        self._app_command = None
        self._app_process = None
        self._start_ts = None

    def start_app(self, cmd_app_prefix=None, cmd_app_prefix_init_timelimit=None, lazy_app_process_detection=False):
        """Starts the application process by instantiating a subprocess invoking the app JAR/executable.

        :param list cmd_app_prefix: Prefix to be prepended to the command starting the application process.
        :param number cmd_app_prefix_init_timelimit: Time limit, in seconds, for the prefix command to start the application process.
        :param boolean lazy_app_process_detection: Whether the `app_process` property should be initialized
            during this method invocation. Should be set to `True` if the property will not be accessed.
        """
        command = []
        cmd_app_prefix_length = 0
        if cmd_app_prefix is not None:
            cmd_app_prefix_length = len(cmd_app_prefix)
            command += cmd_app_prefix

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
        else:
            # Check for bad cases
            raise ValueError(f"{self.config.mode} flag not supported")

        log.info(f"Starting microservice with:\n{' '.join(command)}")
        self._app_command = command[cmd_app_prefix_length:]

        self._start_ts = time.perf_counter()
        self._root_process = subprocess.Popen(command, start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell = False)

        if lazy_app_process_detection:
            self._app_process = None
            return
        self._find_app_process(cmd_app_prefix_init_timelimit)

    def kill_app(self):
        """Stops the app process by sending a SIGTERM signal."""
        if self.root_process is not None:
            root_process_return_code = self.root_process.poll()
            if root_process_return_code is not None:
                raise AppProcessFinishedUnexpectedly(f"Root process terminated prematurely with return code {root_process_return_code}!")
            if self.app_process is None:
                self._find_app_process()
            self.app_process.terminate()
            # Ensure the processes have terminated
            self.root_process.wait(60)

    def _find_app_process(self, time_limit=5):
        """Finds the app process by checking the process subtree of the root process and sets the `app_process` property to the process found.

        :param number time_limit: The time limit for finding the app process.
        """
        app_pid = self._find_cmdline_proc_in_tree(self.root_process.pid, self._app_command, time_limit)
        self._app_process = process_info.get_process(app_pid)

    def _find_cmdline_proc_in_tree(self, root_pid, cmdline, time_limit):
        """Finds the process ID of the process matching the command-line in the process tree of the root process.

        Repeatedly scans through the process tree of the root process trying to match the command-line.
        The lookup is repeated until a time limit is exceeded, at which point all of the processes in
        the process tree are terminated and an exception is raised. Repeating is necessary to allow the
        root process (see option '--cmd-app-prefix') to perform its setup before starting the app process.

        :param number root_pid: Process ID of the root of the process tree which should be searched.
        :param list cmdline: Command-line of the process to be found.
        :param number time_limit: The time limit for finding the process.
        :return: Process ID of the searched for process.
        :rtype: number
        """
        start_time = time.time()
        # time between lookup attempts, in seconds
        retry_grace = 0.001

        tree_root = process_info.get_process(root_pid)
        while time.time() < start_time + time_limit:
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
        raise AppProcessFinishedUnexpectedly(f"Could not find app process using expected cmdline: \"{' '.join(cmdline)}\" after trying for {time_limit} seconds! Terminated all spawned processes!")

    @property
    def config(self):
        return self._config

    @property
    def root_process(self):
        return self._root_process

    @property
    def app_process(self):
        return self._app_process

    @property
    def start_ts(self):
        return self._start_ts

class AppProcessFinishedUnexpectedly(Exception):
    """Used to denote an unexpected termination of the application process."""
    pass
