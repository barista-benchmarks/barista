"""Builds the Barista benchmarks."""
from argparse import ArgumentParser
import logging as log
import os
import subprocess_runner
from vm import get_vm
from benchmark_registry import BenchmarkRegistry

class Builder:
    """Builds the Barista benchmarks."""
    def __init__(self, benchmark_registry):
        self._benchmark_registry = benchmark_registry

    def build(self, selection, skip_nib_generation, get_jar, get_nib, maven_options):
        """Builds a selection of Barista benchmarks.

        :param list selection: User specified list of Barista benchmark names that should be built, can be empty which means all benchmarks should be built.
        :param boolean skip_nib_generation: Whether the step of generating native image bundles should be skipped.
        :param boolean get_jar: Whether to just print the path of the built jar without building anything.
        :param boolean get_nib: Whether to just print the path of the built nib (Native Image Bundle) file without building anything.
        :param str maven_options: Additional options to pass to mvn when building maven projects.
        """
        selection = selection if selection else self._benchmark_registry.benchmark_names
        success_count = 0
        failure_list = []
        for bench_name in selection:
            build_successful = self._build_benchmark(bench_name, skip_nib_generation, get_jar, get_nib, maven_options)
            if build_successful:
                success_count += 1
            else:
                failure_list.append(bench_name)
        log.info(f"{success_count}/{len(selection)} successfully built")
        if failure_list:
            raise ChildProcessError(f"Following benchmarks could not be built: {', '.join(failure_list)}")

    def _build_benchmark(self, bench_name, skip_nib_generation, get_jar, get_nib, maven_options):
        """Builds a Barista benchmark, by invoking its "build.sh" script.

        :param string bench_name: Name of the Barista benchmark that should be built.
        :param boolean skip_nib_generation: Whether the step of generating a native image bundle should be skipped.
        :param boolean get_jar: Whether to just print the path of the built jar without building anything.
        :param boolean get_nib: Whether to just print the path of the built nib (Native Image Bundle) file without building anything.
        :param str maven_options: Additional options to pass to mvn when building maven projects.
        :return: Whether the build was successful.
        :rtype: boolean
        """
        build_script = os.path.join(self._benchmark_registry.benchmarks_dir, bench_name, "build.sh")
        cmd = [build_script]
        if skip_nib_generation:
            cmd.append("--skip-nib-generation")
        if get_jar:
            cmd.append("--get-jar")
        if get_nib:
            cmd.append("--get-nib")
        if maven_options:
            cmd.append(f"--maven-options={maven_options}")
        log.info(f"Building benchmark {bench_name} by running \"{' '.join(cmd)}\"")
        try:
            subprocess_runner.run(cmd, capture_output=False)
        except ChildProcessError as e:
            log.error(f"Build of benchmark {bench_name} failed!")
            log.error(e)
            return False
        log.info(f"Build of benchmark {bench_name} succeeded!")
        return True

def parse_arguments(benchmark_names):
    """Parses arguments needed for building Barista benchmarks.

    :return: Object holding parsed arguments.
    :rtype: argparse.Namespace
    """
    parser = ArgumentParser(prog="build")
    # not defining `choices=benchmark_names` here since there is an issue in how `nargs="*"` interacts with it https://github.com/python/cpython/pull/92565
    # the issue has been fixed starting from python 3.12
    parser.add_argument("bench_list", metavar="bench-name", nargs="*", help="name(s) of the benchmark(s) to be built, all are built if unspecified")
    parser.add_argument("-s", "--skip-nib-generation", action="store_true", help="skip building nibs (Native Image Bundles), only build the jars")
    parser.add_argument("-j", "--get-jar", action="store_true", help="prints the path of the built jar without building anything. The path will be printed in the pattern of 'application jar file path is: <path>\n'")
    parser.add_argument("-n", "--get-nib", action="store_true", help="prints the path of the built nib (Native Image Bundle) file without building anything. The path will be printed in the pattern of 'application nib file path is: <path>\n'")
    parser.add_argument("-m", "--maven-options", help="additional options to pass to mvn when building maven projects")
    parser.add_argument("-d", "--debug", action="store_true", help="show debug logs")
    args = parser.parse_args()

    # verifying the benchmark choices manually here because of the problematic interaction between nargs and choices in argparse
    for bench_name in args.bench_list:
        if bench_name not in benchmark_names:
            raise ValueError(f"Invalid benchmark choice in \"{bench_name}\"! The benchmark selection is: [{', '.join(benchmark_names)}].")
    return args

def main():
    benchmark_registry = BenchmarkRegistry()
    args = parse_arguments(benchmark_registry.benchmark_names)
    log.basicConfig(level="DEBUG" if args.debug else "INFO")

    if not args.get_nib and not args.get_jar:
        java_home = os.getenv("JAVA_HOME")
        vm = get_vm(java_home)
        log.info(f"Version of the available JVM at JAVA_HOME:\n{vm.version}")
        if not vm.contains_executable("java"):
            raise ValueError("'java' not found in your JAVA_HOME! Please set the JAVA_HOME environment variable so it points to a JVM distribution.")
        if not args.skip_nib_generation and not vm.contains_executable("native-image"):
            raise ValueError("'native-image' not found in your JAVA_HOME! Either change your JAVA_HOME so it points to a GraalVM distribution or add '--skip-nib-generation' so native image bundles aren't generated.")

    builder = Builder(benchmark_registry)
    builder.build(args.bench_list, args.skip_nib_generation, args.get_jar, args.get_nib, args.maven_options)

if __name__ == "__main__":
    main()