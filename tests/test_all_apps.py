"""Basic functionality tests of the Barista benchmark suite."""
import sys
import os
import re
import logging as log
import subprocess
from benchmark_registry import BenchmarkRegistry

class AppTester:
    """Runs commands that build/benchmark a specific app and verifies their normal termination."""
    def __init__(self, name, barista_build_script, barista_harness_script, native_mode):
        self._name = name
        self._barista_build_script = barista_build_script
        self._barista_harness_script = barista_harness_script
        self._native_mode = native_mode

    def build(self):
        """Runs a command that builds the app and verifies that it terminates normally."""
        cmd = [self._barista_build_script, self._name] + self.get_extra_build_options()
        log.info(f"Building the jar/nib (Native Image Bundle) files for '{self._name}' using '{' '.join(cmd)}'.")
        proc = subprocess.run(cmd)
        assert proc.returncode == 0

    def verify_build_artifact(self):
        """Runs a command that prints the path to the build artifact, captures that path, and then verifies if the artifact actually exists."""
        cmd = [self._barista_build_script, self._name]
        if not self._native_mode:
            cmd += ["--get-jar"]
            pattern = r"application jar file path is: ([^\n]+)\n"
        else:
            cmd += ["--get-nib"]
            pattern = r"application nib file path is: ([^\n]+)\n"
        log.info(f"Verifying that the build artifact was produced for '{self._name}' using '{' '.join(cmd)}'.")
        proc = subprocess.run(cmd, stdout=subprocess.PIPE)
        assert proc.returncode == 0
        m = re.search(pattern, proc.stdout.decode("utf-8"))
        if not m:
            raise ValueError(f"Could not extract the app build artifact from the command output! Expected to match pattern {repr(pattern)}.")
        assert os.path.isfile(m.group(1))

    def benchmark_in_JVM_mode(self, options=[]):
        """Runs a command that benchmarks the app in JVM mode and verifies that it terminates normally.

        :param list options: Additional options to append to the command.
        """
        cmd = [self._barista_harness_script, self._name, "-m", "jvm"] + options
        log.info(f"Running benchmark against {self._name} in JVM mode using '{' '.join(cmd)}'.")
        proc = subprocess.run(cmd)
        assert proc.returncode == 0

    def benchmark_in_native_mode(self, options=[]):
        """Runs a command that benchmarks the app in native mode and verifies that it terminates normally.

        :param list options: Additional options to append to the command.
        """
        cmd = [self._barista_harness_script, self._name, "-m", "native"] + options
        log.info(f"Running benchmark against {self._name} in native mode using '{' '.join(cmd)}'.")
        proc = subprocess.run(cmd)
        assert proc.returncode == 0

    def get_extra_build_options(self):
        if not self._native_mode:
            return self.get_extra_JVM_build_options()
        return self.get_extra_native_build_options()

    def get_extra_JVM_build_options(self):
        return ["-s"]

    def get_extra_native_build_options(self):
        return []

def _get_harness_script(script_name):
    """Returns the path to a Barista harness script, verifying that the file exists.

    :param string script_name: Name of the script.
    :return: Absolute path to the script file.
    :rtype: os.path
    """
    root_dir = os.path.dirname(os.path.dirname(__file__))
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"The Barista root directory path '{root_dir}' does not point to a directory!")
    script = os.path.abspath(os.path.join(root_dir, script_name))
    if not os.path.isfile(script):
        raise FileNotFoundError(f"'{script_name}' script does not exist in the Barista root directory '{root_dir}'.")
    return script

def _get_all_apps_excluding(exclude_list=[]):
    return [app for app in BenchmarkRegistry().benchmark_names if app not in exclude_list]

_QUICK_BENCH_OPTIONS = ["--warmup-duration", "1", "--throughput-duration", "1", "--latency-duration", "1"]
_QUICK_NATIVE_OPTIONS = ["-b=-Ob", "--startup-timeout", "30"]

def test_build_and_JVM_benchmark():
    """Tests that all apps present in the Barista benchmark suite can be built and benchmarked in JVM mode."""
    barista_build_script = _get_harness_script("build")
    barista_harness_script = _get_harness_script("barista")
    apps = _get_all_apps_excluding()
    log.info(f"Testing that all the apps {apps} can be built and benchmarked in JVM mode.")
    for app in apps:
        app_tester = AppTester(app, barista_build_script, barista_harness_script, False)
        app_tester.build()
        app_tester.verify_build_artifact()
        app_tester.benchmark_in_JVM_mode(options=_QUICK_BENCH_OPTIONS)
    log.info("Every app can be built and benchmarked in JVM mode.")

def test_build_and_native_benchmark():
    """Tests that all apps present in the Barista benchmark suite can be built and benchmarked in native mode."""
    barista_build_script = _get_harness_script("build")
    barista_harness_script = _get_harness_script("barista")
    apps = _get_all_apps_excluding()
    log.info(f"Testing that all the apps {apps} can be built and benchmarked in native mode.")
    for app in apps:
        app_tester = AppTester(app, barista_build_script, barista_harness_script, True)
        app_tester.build()
        app_tester.verify_build_artifact()
        app_tester.benchmark_in_native_mode(options=_QUICK_BENCH_OPTIONS + _QUICK_NATIVE_OPTIONS)
    log.info("Every app can be built and benchmarked in native mode.")