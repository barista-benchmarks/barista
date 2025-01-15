import logging as log
import os

class BenchmarkRegistry:
    """Registry of Barista benchmark information."""
    def __init__(self):
        self._benchmarks_dir = None
        self._benchmark_names = None

    @property
    def benchmarks_dir(self):
        if not self._benchmarks_dir:
            self._benchmarks_dir = self._get_benchmarks_dir()
        return self._benchmarks_dir

    @property
    def benchmark_names(self):
        if not self._benchmark_names:
            self._benchmark_names = self._get_benchmark_names()
        return self._benchmark_names

    def get_benchmark_dir(self, bench_name):
        """Return the absolute path to the specified Barista benchmark's root directory.

        :param string bench_name: Name of the Barista benchmark.
        """
        if bench_name not in self.benchmark_names:
            raise ValueError(f"Benchmark '{bench_name}' is not a part of the Barista benchmark suite!")
        return os.path.join(self.benchmarks_dir, bench_name)

    def _get_benchmarks_dir(self):
        """Returns the absolute path to the "benchmarks" directory in the Barista repo."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "benchmarks"))

    def _get_benchmark_names(self):
        """Returns a list of benchmark names for the Barista benchmark suite.

        Compiles a list of benchmark names by iterating through the subdirectories of the "benchmarks" directory,
        adding the names of those subdirectories which contain a "build.sh" script.
        """
        benchmark_names = []
        for bench_name in os.listdir(self.benchmarks_dir):
            if self._verify_benchmark_dir(bench_name):
                benchmark_names.append(bench_name)
        if not benchmark_names:
            raise FileNotFoundError("No benchmarks found!")
        return sorted(benchmark_names)

    def _verify_benchmark_dir(self, bench_name):
        """Verifies that the benchmark directory exists and contains a build.sh script.

        :param string bench_name: Name of the benchmark.
        :return: Whether the benchmark directory exists and contains a build.sh script.
        :rtype: boolean
        """
        bench_dir = os.path.join(self.benchmarks_dir, bench_name)
        if not os.path.isdir(bench_dir):
            return False
        bench_build_script = os.path.join(bench_dir, "build.sh")
        if not os.path.isfile(bench_build_script):
            return False
        return True