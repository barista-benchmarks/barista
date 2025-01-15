import subprocess
import logging as log

def run(cmd, capture_output=True):
    log.info(f"Running the following command in a subprocess:\n{' '.join(cmd)}")
    if capture_output:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        proc = subprocess.run(cmd)
    if capture_output and proc.stdout:
        log.info(f"Dumping the stdout of the subprocess:\n{proc.stdout.decode('utf-8')}")
    if proc.returncode:
        if capture_output and proc.stderr:
            log.error(f"Dumping the stderr of the subprocess:\n{proc.stderr.decode('utf-8')}")
        raise ChildProcessError(f"Subprocess failed with return code: {proc.returncode}! The subprocess was executing the following command:\n{' '.join(cmd)}")
    # The bash shell, with the -x option set, prints the trace of commands to stderr
    if capture_output and proc.stderr:
        log.info(f"Dumping the stderr of the subprocess:\n{proc.stderr.decode('utf-8')}")
    return proc
