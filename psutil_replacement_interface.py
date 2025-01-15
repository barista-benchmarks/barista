"""Defines the process management and resource utilization interface necessary for the Barista harness."""
from abc import ABC, abstractmethod

class ProcessInterface(ABC):
    """Represents an OS process with the given pid."""
    @abstractmethod
    def __init__(self, pid):
        pass

    @abstractmethod
    def memory_info(self):
        """Get current memory information about the process.

        :return: Current memory information about the process.
        :rtype: MemoryInfo
        """
        pass

    @abstractmethod
    def cpu_percent(self, interval):
        """Return a float representing the current system-wide CPU utilization as a percentage.

        :param float interval: The time interval for which CPU utilization is to be collected.
        :return: Current system-wide CPU utilization as a percentage.
        :rtype: float
        """
        pass

    @abstractmethod
    def children(self, recursive):
        """Return the children or all descendants of this process.

        :param bool recursive: Whether to return all descendants of this process.
        :return: The children/descendants as a list of ProcessInterface instances.
        :rtype: list[ProcessInterface]
        """
        pass

    @abstractmethod
    def cmdline(self):
        """Return the command line this process has been called with.

        :rtype: list[str]
        """
        pass

    @abstractmethod
    def terminate(self):
        """Terminate the process with SIGTERM signal."""
        pass

class MemoryInfo():
    """Structure containing process memory information required by Barista such as rss (Resident Set Size) and vms (Virtual Memory Size)."""
    def __init__(self, rss, vms):
        self._rss = rss
        self._vms = vms

    @property
    def rss(self):
        return self._rss

    @property
    def vms(self):
        return self._vms