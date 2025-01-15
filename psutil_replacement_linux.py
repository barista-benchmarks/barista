"""Implements process management and resource utilization methods for the Linux platform."""
from psutil_replacement_interface import ProcessInterface, MemoryInfo
import logging as log
import mmap
import time
import os
import signal

class Process(ProcessInterface):
    """Represents a Linux process with the given pid."""
    def __init__(self, pid):
        self._pid = int(pid)
        self._previous_cpu_times = None

    @property
    def pid(self):
        return self._pid

    def memory_info(self):
        try:
            with open(f"/proc/{self.pid}/stat", "r") as f:
                stat = f.read()    # process information as a string, bits of information separated by spaces
            stat = stat.split(" ") # process information as an array
            rss = int(stat[23]) * mmap.PAGESIZE
            vms = int(stat[22])
            return MemoryInfo(rss, vms)
        except FileNotFoundError as file_not_found:
            log.debug(f"process PID not found (pid={self.pid}) as proc file '{file_not_found.filename}' does not exist")
            raise

    def cpu_percent(self, interval):
        try:
            previous_cpu_times, current_cpu_times = self._poll_previous_and_current_cpu_times()
            if interval:
                time.sleep(interval)
                previous_cpu_times, current_cpu_times = self._poll_previous_and_current_cpu_times()
            percentage = self._calculate_cpu_percent(previous_cpu_times, current_cpu_times)
            return percentage
        except FileNotFoundError as file_not_found:
            log.debug(f"process PID not found (pid={self.pid}) as proc file '{file_not_found.filename}' does not exist")
            raise

    def children(self, recursive):
        try:
            proc_tree_search_lst = [self]
            children = []
            while proc_tree_search_lst:
                current_proc = proc_tree_search_lst.pop(0)
                current_pid = current_proc.pid
                for thread in os.listdir(f"/proc/{current_pid}/task"):
                    with open(f"/proc/{current_pid}/task/{thread}/children", "r") as f:
                        children_of_thread = f.read()
                    children_of_thread = children_of_thread.split(" ")
                    children_of_thread = list(filter(None, children_of_thread))
                    children_of_thread = [Process(child_pid) for child_pid in children_of_thread]
                    children += children_of_thread
                    if recursive:
                        proc_tree_search_lst += children_of_thread
            return children
        except FileNotFoundError as file_not_found:
            log.debug(f"process PID not found (pid={self.pid}) as proc file '{file_not_found.filename}' does not exist")
            raise

    def cmdline(self):
        try:
            with open(f"/proc/{self.pid}/cmdline", "r") as f:
                cmdline = f.read()                                   # the whole cmdline as a string, words separated by '\0' characters
            cmdline_list = cmdline.split("\0")                       # list of cmdline words, may contain empty strings
            cmdline_without_empty = list(filter(None, cmdline_list)) # list of non-empty cmdline words
            return cmdline_without_empty
        except FileNotFoundError as file_not_found:
            log.debug(f"process PID not found (pid={self.pid}) as proc file '{file_not_found.filename}' does not exist")
            raise

    def terminate(self):
        os.kill(self.pid, signal.SIGTERM)

    def _poll_previous_and_current_cpu_times(self):
        """Collects current CPU utilization and returns it alongside the previous CPU utilization information.

        The current CPU utilization information is saved in the _previous_cpu_times field, overwriting the previous
        measurement, so it can be returned as the previous measurement during the next invocation of this method.

        :return: Previous and current CPU utilization measurements.
        :rtype: (CPUTimes, CPUTimes)
        """
        previous_cpu_times = self._previous_cpu_times
        current_cpu_times = self._get_current_cpu_times()
        self._previous_cpu_times = current_cpu_times
        return previous_cpu_times, current_cpu_times

    def _get_current_cpu_times(self):
        """Returns the current CPU utilization information.

        :rtype: CPUTimes
        """
        with open(f"/proc/{self.pid}/stat", "r") as f:
            stat = f.read()         # process information as a string, bits of information separated by spaces
        stat = stat.split(" ")      # process information as an array
        user_time = int(stat[13])   # time spent in user mode, in clock ticks
        kernel_time = int(stat[14]) # time spent in kernel mode, in clock ticks
        timestamp = time.time()    # epoch time, in seconds
        return CPUTimes(user_time, kernel_time, timestamp)

    def _calculate_cpu_percent(self, start_times, end_times):
        """Calculates CPU utilization during a time interval as a percentage.

        The CPU utilization percentage for the interval is calculated by dividing the time the CPU was used by the process
        during the interval with the interval duration.

        :param CPUTimes start_times: CPU utilization information at the start of the measurement interval.
        :param CPUTimes end_times: CPU utilization information at the end of the measurement interval.
        :return: CPU utilization during a time interval as a percentage.
        :rtype: float
        """
        if not start_times:
            return 0.0
        usage_time_during_interval = end_times.total_time - start_times.total_time # total time the process was using the cpu during the interval
        interval_duration = end_times.timestamp - start_times.timestamp            # measurement interval duration
        return 100.0 * usage_time_during_interval / interval_duration

class CPUTimes():
    """Structure containing accumulated process times, in seconds."""
    def __init__(self, user_time, kernel_time, timestamp):
        """Constructs a CPUTimes instance, converting clock ticks into seconds.

        :param number user_time: Process time spent in user mode, in clock ticks.
        :param number kernel_time: Process time spent in kernel mode, in clock ticks.
        :param number timestamp: Epoch time, in seconds.
        """
        self._user_time = user_time / self.clock_frequency()
        self._kernel_time = kernel_time / self.clock_frequency()
        self._timestamp = timestamp

    _clock_frequency = None

    @classmethod
    def clock_frequency(cls):
        """Get clock frequency from the system configuration file, in hertz."""
        if not cls._clock_frequency:
            cls._clock_frequency = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
        return cls._clock_frequency

    @property
    def user_time(self):
        return self._user_time

    @property
    def kernel_time(self):
        return self._kernel_time

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def total_time(self):
        """Total time process was utilizing the CPU, calculated by adding up user and kernel time."""
        return self.user_time + self.kernel_time