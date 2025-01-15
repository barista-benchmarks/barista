"""Resolves the process management implementation for the platform we're running on.

Returns a custom implementation for Linux and the psutil package for other platforms.
"""
import sys
import psutil_replacement_linux

def get_process(pid):
    """Returns an OS corresponding object representing the OS process.

    :param number pid: Process identifier of the process to retrieve.
    """
    if sys.platform.startswith("linux"):
        return psutil_replacement_linux.Process(pid)
    try:
        import psutil
        return psutil.Process(pid)
    except ImportError:
        log.error("Please install the 'psutil' package. You can do so by running:\n\tpip install psutil")
        raise