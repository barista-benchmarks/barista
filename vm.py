import subprocess_runner
import logging as log
import os
import re
import subprocess

def get_vm(java_home):
    """Returns a VM object corresponding to the type of JVM distribution at java_home.

    :param os.path java_home: The root directory of the JVM distribution.
    """
    _verify_java_home(java_home)

    try:
        vm = NativeImageVM(java_home)
    except MissingExecutableFileException:
        log.debug("Java home does not point to a GraalVM distribution.")
        vm = JVM(java_home)
    return vm

def _verify_java_home(java_home):
    """Verifies that java_home is defined and points to a directory."""
    if not java_home:
        raise ValueError("Java home is not defined!")
    log.info(f"Java home is pointing to \"{java_home}\".")
    if not os.path.isdir(java_home):
        raise NotADirectoryError("Java home does not point to an existing directory!")

class VM:
    def __init__(self, java_home, executable_names):
        self._java_home = java_home
        self._executable_names = executable_names
        self._version = None
        self._verify_executables()

    @property
    def java_home(self):
        return self._java_home

    @property
    def executables(self):
        return self._executables

    @property
    def version(self):
        if not self._version:
            self._version = self._get_version_info()
        return self._version

    def contains_executable(self, executable_name):
        return executable_name in self.executables

    def _get_version_info(self):
        """Gets version information of all the VM executables."""
        version_infos = []
        for executable in self.executables.values():
            executable_version_info = self._get_executable_version_info(executable)
            version_infos.append(executable_version_info)
        return ''.join(version_infos)

    def _verify_executables(self):
        """Verifies that java home contains the executable files."""
        executables_dict = {}
        for executable_name in self._executable_names:
            executable = self._get_file(executable_name)
            executables_dict[executable_name] = executable
        self._executables = executables_dict

    def _get_file(self, file_name):
        """Returns the file from the java home's binary directory, after verifying that it exists.

        :param string file_name: Name of the file.
        :return: Absolute path to the VM file.
        :rtype: os.path
        """
        file = os.path.join(self.java_home, "bin", file_name)
        if not os.path.isfile(file):
            raise MissingExecutableFileException(f"Could not find '{file}'!")
        return file

    def _get_executable_version_info(self, executable):
        """Gets version information of the executable.

        :param os.path executable: The executable for which we get version information.
        """
        cmd = [executable, "--version"]
        log.info(f"Getting platform version information with command \"{' '.join(cmd)}\"")
        proc = subprocess.run(cmd, stdout=subprocess.PIPE)
        if proc.returncode != 0:
            raise ChildProcessError(f"Command \"{' '.join(cmd)}\" failed with return code {proc.returncode}!")
        output = proc.stdout.decode("utf-8")
        return output

class MissingExecutableFileException(Exception):
    pass

class JVM(VM):
    def __init__(self, java_home):
        super(JVM, self).__init__(java_home, ["java"])

class NativeImageVM(VM):
    def __init__(self, java_home):
        super(NativeImageVM, self).__init__(java_home, ["java", "native-image"])

    def native_image_build(self, nib_file, image_name, build_options, verify_app_image_existance=True):
        """Builds the app native image from the app Native Image Bundle file.

        :param os.path nib_file: Path of the Native Image Bundle to build.
        :param string image_name: Name of the image to build.
        :param list build_options: Additional options to be propagated to the native image build command.
        :param boolean verify_app_image_existance: Whether to verify the existance of the app image file.
        :return: Absolute path to the newly built native image.
        :rtype: os.path
        """
        output_dir = nib_file[:-4] + ".output"
        image_path = os.path.join(output_dir, "default", image_name)
        if os.path.isfile(image_path):
            log.info(f"Deleting previously built native image located at \"{image_path}\"")
            os.remove(image_path)
        cmd = [self.executables["native-image"], f"--bundle-apply={nib_file}", "-g", "-o", image_name] + build_options
        log.info(f"Building native image using command: \"{' '.join(cmd)}\"")
        subprocess_runner.run(cmd, capture_output=False)
        if verify_app_image_existance and not os.path.isfile(image_path):
            raise FileNotFoundError(f"Native image not found at expected location: \"{image_path}\"!")
        log.info(f"Native image \"{image_path}\" was successfully built!")
        return image_path