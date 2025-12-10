from abc import abstractmethod
import shutil

def cmd_exists(cmd, path=None):
    ''' Checks if a command exists'''
    return shutil.which(cmd, path=path) is not None

class AbstractLoadGenerator:
    @abstractmethod
    def measure(self):
        '''
        Main method of load generator. Used for starting subprocess.
        Returns a pair of key and value. Key is either throughput or latency.
        Value is map of results.
        '''
        pass

    @abstractmethod
    def parse_measurements(self):
        '''Parse the stdout of process of load. '''
        pass

    @abstractmethod
    def dump_stdout(self):
        '''Dump stdout of load process'''
        pass

    @abstractmethod
    def cleanup(self):
        '''Cleanup method for load generators'''
        pass
