## Contribution Guide

This document will provide a high-level overview of how to contribute to Barista Benchmark Suite.

### Setting up your environment

After following [the steps to install hard dependencies](README.md#dependencies) (such as `wrk` and `wrk2`, but also `psutil` if you're not using an OS based on Linux) you should also install developer dependencies:
```console
pip install -e '.[dev]'
```

### Testing

This project uses the [pytest](https://docs.pytest.org/en/stable/) testing framework.
Tests are located in the `tests` subdirectory of the root directory of the repository.
Tests are provided to facilitate catching obvious breaking changes, and a successful execution should not be taken as a guarantee that a change does not introduce issues.
You can run all the tests with the command:
```console
python3 -m pytest --log-cli-level=INFO
```
or, alternatively, you can run the `run_tests.sh` script:
```console
./run_tests.sh
```
which also ensures the virtual environment is properly set up.

If you wish to run a subset of the tests, e.g. only the ones containing 'JVM' in their name, you can run the command:
```console
python3 -m pytest --log-cli-level=INFO -k 'JVM'
```