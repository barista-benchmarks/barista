"""Prepares a microservice app for benchmarking and configures and invokes the Barista harness.

This script includes functions and classes that facilitate the benchmarking of apps.
The preparation comprises the formation of the harness configuration and the retrieval of the application executable.
The formation of the harness configuration is handled by the Configuration class, defined in the 'configuration.py' file.
The app executable retrieval process involves fetching the app jar/nib archive. In the case of the 'native' execution mode,
the app native image is built from the previously fetched nib.
This script offers an interface to the user through which they can easily perform benchmarks. Example:
    python barista.py micronaut-hello-world
The interface offers an extensive set of options, enabling easy configuration of the Barista harness. View all of the options using:
    python barista.py --help
"""

from benchmark_registry import BenchmarkRegistry
from configuration import Configuration, ServiceMode
from load_tester import Benchmark
import subprocess_runner
import process_info
import logging as log
import os
import re
import signal
import sys
import shutil
from vm import get_vm, NativeImageVM

class AppExecutableSupplier:
    """Supplies the app executable, fetching, and possibly building, the executable file, depending on the execution mode."""
    artifact_group = "artifact"
    image_name_group = "image_name"

    def __init__(self, config, vm):
        self._config = config
        self._vm = vm

    def supply_executable(self):
        """Supplies the app executable, fetching, and possibly building, the executable file, depending on the execution mode.

        :return: Path to the app executable.
        :rtype: os.path
        """
        archive_dict = self._fetch_build_artifact()
        if self._config.mode == ServiceMode.JVM:
            return archive_dict[AppExecutableSupplier.artifact_group]
        image_path = self._build_native_image(archive_dict)
        self._verify_app_image_file(image_path)
        return image_path

    def _fetch_build_artifact(self):
        """Executes a fetch command of the "build.sh" script of the microservice app and returns a dictionary containing the path to the build artifact and potentially application specific information.

        :return: Dictionary containing the path to the build artifact and any app specific information.
        :rtype: dict
        """
        app_dir = self._config.benchmark_registry.get_benchmark_dir(self._config.bench_name)
        app_build_script = os.path.join(app_dir, "build.sh")
        cmd = [app_build_script]
        if self._config.mode == ServiceMode.JVM:
            cmd.append("--get-jar")
            output_pattern = f"application jar file path is: (?P<{AppExecutableSupplier.artifact_group}>[^\n]+)\n"
        if self._config.mode == ServiceMode.NATIVE:
            cmd.append("--get-nib")
            output_pattern = f"application nib file path is: (?P<{AppExecutableSupplier.artifact_group}>[^\n]+)\n(?:fixed image name is: (?P<{AppExecutableSupplier.image_name_group}>[^\n]+)\n)?"
        log.info(f"Locating the app build artifact with command \"{' '.join(cmd)}\"")
        proc = subprocess_runner.run(cmd)
        output_match = re.search(output_pattern, proc.stdout.decode("utf-8"))
        if not output_match:
            raise ValueError(f"Could not extract the app build artifact from the command output! Expected to match pattern {repr(output_pattern)}.")
        match_dict = output_match.groupdict()
        app_exec_path = match_dict[AppExecutableSupplier.artifact_group]
        if not os.path.isfile(app_exec_path):
            barista_build_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "build"))
            raise FileNotFoundError(f"App build artifact could not be found at \"{app_exec_path}\". Make sure you've previously built the application, you can use the command:\n\t{barista_build_script} {self._config.bench_name}")
        return match_dict

    def _build_native_image(self, nib_dict):
        """Builds the app native image from the app Native Image Bundle file.

        Potentially copies the built app image as a workaround to a known GraalVM Native Image bug.

        :param os.path nib_dict: Dictionary containing path of the Native Image Bundle to build and potentially a hard-coded image name.
        :return: Absolute path to the newly built native image.
        :rtype: os.path
        """
        assert isinstance(self._vm, NativeImageVM)
        image_path = self._vm.native_image_build(nib_dict[AppExecutableSupplier.artifact_group], self._config.bench_name, build_options=self._config.build_options, verify_app_image_existance=False)
        if nib_dict.get(AppExecutableSupplier.image_name_group) is None:
            return image_path

        # because of a graal issue in handling image build args in the intended order
        # we need to rename the app image
        desired_image_path = image_path
        actual_image_path = os.path.join(os.path.dirname(desired_image_path), nib_dict.get(AppExecutableSupplier.image_name_group))
        if os.path.isfile(actual_image_path) and not os.path.isfile(desired_image_path):
            log.debug(f"Moving the app image from '{actual_image_path}' to '{desired_image_path}'")
            shutil.move(actual_image_path, desired_image_path)
        return desired_image_path

    def _verify_app_image_file(self, image_path):
        """Verifies the existance of the app image file.

        :param os.path image_path: Absolute path to the app image file.
        """
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"App image not found at '{image_path}'!")

class BenchmarkHarness:
    """Manages the preparation, execution and cleanup of the benchmark.

    The harness executes the following steps, in order:
    1. prepare (optional)
    2. execute
    3. cleanup (optional)

    The prepare step is performed first, as long as the 'prepare.sh' script exists
    in the benchmark directory. The prepare step is skipped if no such script
    exists or if the '--skip-prepare' CLI option is set. The prepare step is
    intended for any tasks that are necessary in order for the app to function
    correctly during the execution step (e.g. starting any auxilliary services
    that the app communicates during execution). Some apps may require some
    information to be propagated from the prepare step to the execution step.
    In order to enable this propagation a 'barista-execution-context' file may
    be created during the prepare step. This file will be later parsed in the
    execution step. The 'barista-execution-context' file should be a toml file
    containing at least one of the following fields:
    - app-args
    - vm-options
    with a string value assigned. An example of the 'barista-execution-context'
    file:
    ================================ barista-execution-context
    generated = 2024-11-19 14:22:27
    vm-options = "-Dopt1=val1 -Dopt2=val2 -Dopt3=val3"
    ================================
    Where:
    - 'generated':
        - is assigned a timestamp taken at the moment of file creation
        - this field is ignored by the harness
    - 'vm-options':
        - is assigned a string value containing all of the VM options that
          should be propagated to the app during the execution step
        - these options are concatenated to the VM options specified in the
          CLI/config file

    The execution step is performed after the optional prepare step. The
    execution step is influenced not only by the CLI/config file options, but
    also by the 'barista-execution-context' file, if one is present in the
    directory of the currently running benchmark.

    The cleanup step is performed last, as long as the 'cleanup.sh' script
    exists in the benchmark directory. The cleanup step is skipped if no such
    script exists or if the '--skip-cleanup' CLI option is set. The purpose of
    the cleanup step is to ensure the system is left in the same state it was
    in before benchmarking. All the resources acquired during the prepare step
    should be released (e.g. the auxilliary services should be stopped, the
    'barista-execution-context' file should be deleted).
    """
    def __init__(self, config):
        self._config = config
        self._benchmark = None

    def run(self):
        self.run_prepare_if_exists()
        try:
            self.execute_benchmark()
        finally:
            self.run_cleanup_if_exists()
        self.final_report()

    def run_prepare_if_exists(self):
        prepare_script = os.path.join(self._config.benchmark_registry.get_benchmark_dir(self._config.bench_name), "prepare.sh")
        if os.path.isfile(prepare_script) and not self._config.skip_prepare:
            log.info("Running the prepare script...")
            subprocess_runner.run([prepare_script], capture_output=False)
            self._config.update_after_benchmark_prepare()

    def execute_benchmark(self):
        self._benchmark = Benchmark(self._config)
        def _signal_handler(sig, frame):
            log.info("SIGINT detected cleaning up...")
            self._benchmark._cleanup()
            sys.exit(0)
        signal.signal(signal.SIGINT, _signal_handler)
        self._benchmark.run()

    def run_cleanup_if_exists(self):
        cleanup_script = os.path.join(self._config.benchmark_registry.get_benchmark_dir(self._config.bench_name), "cleanup.sh")
        if os.path.isfile(cleanup_script) and not self._config.skip_cleanup:
            log.info("Running the cleanup script...")
            subprocess_runner.run([cleanup_script])

    def final_report(self):
        self._benchmark.print_final_report_to_stdout()

def main():
    benchmark_registry = BenchmarkRegistry()
    config = Configuration(benchmark_registry)
    log.info(f"Running Barista harness with args: {sys.argv}")

    # verify process management setup
    process_info.get_process(os.getpid())

    # verify JVM distribution
    # provided with --java-home option or JAVA_HOME environment variable
    try:
        vm = get_vm(config.java_home)
        log.info(f"Version of the available JVM at java home:\n{vm.version}")
    except Exception:
        # If the user provided a natively-executable app, then no VM is necessary
        if config.mode != ServiceMode.NATIVE or config.app_executable is None:
            raise
    if config.mode == ServiceMode.JVM and not vm.contains_executable("java"):
        raise ValueError("'java' not found in your java home! Please provide a JVM distribution by using the '--java-home' option or setting the JAVA_HOME environment variable.")
    if config.mode == ServiceMode.NATIVE and config.app_executable is None and not vm.contains_executable("native-image"):
        raise ValueError("'native-image' not found in your java home! In order to benchmark the app in the 'native' execution mode please provide a GraalVM distribution by using the '--java-home' option or setting the JAVA_HOME environment variable. Alternatively, you could provide the app executable using the '--app-executable' option.")

    if not config.app_executable:
        supplier = AppExecutableSupplier(config, vm)
        config.app_executable = supplier.supply_executable()

    harness = BenchmarkHarness(config)
    harness.run()

if __name__ == "__main__":
    main()