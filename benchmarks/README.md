# Barista Suite Applications

This directory contains the application selection for the Barista benchmark suite.
Each subdirectory in this directory represents a single application.

## Application directory contract

There are a few rules each application subdirectory should abide by - each application subdirectory should:
- contain a `build.sh` script
    ```
    Builds the project jar and then uses GraalVM to generate a nib file (Native Image Bundle)

    usage: build.sh [--help] [--skip-nib-generation] [--get-jar] [--get-nib] [--maven-options=MAVEN_OPTIONS]

    options:
        --help                           shows this help message and exits
        --skip-nib-generation            skips building the application nib (Native Image Bundle) file, only builds the jar
        --get-jar                        prints the path of the built jar without building anything. The path will be printed in the pattern of 'application jar file path is: <path>\n'
        --get-nib                        prints the path of the built nib (Native Image Bundle) file without building anything. The path will be printed in the pattern of 'application nib file path is: <path>\n'
        --maven-options=MAVEN_OPTIONS    additional options to pass to mvn when building maven projects

    ```
- contain a `default.barista.json` workload configuration JSON file in a `workloads` subdirectory
    - configures the load-testing phases and the load-tester in general
    ```
    {
        "endpoint": "http://127.0.0.1:8000/hello",
        "output_dir": "logs/",
        "load_testing":{
            "connections": 1,
            "threads": 1,
            "startup":{
                "iterations": 10
            },
            "warmup":{
                "iterations": 1,
                "iteration_time_seconds": 90
            },
            "throughput":{
                "iterations": 1,
                "iteration_time_seconds": 60
            },
            "latency_measurement":{
                "iterations": 1,
                "iteration_time_seconds": 60,
                "search_strategy": "FIXED",
                "rates": 15000
            }
        }
    }
    ```
- (OPTIONAL) contain application source code (structure is not of importance)
    - the `build.sh` script that generates the jar and nib files generally necessitates the presence of the application source code
- (OPTIONAL) contain a `prepare.sh` script
    - is intended for any tasks that are necessary in order for the app to function
    correctly during the execution step (e.g. starting any auxilliary services
    that the app communicates during execution). Some apps may require some
    information to be propagated from the prepare step to the execution step.
    In order to enable this propagation a 'barista-execution-context' file may
    be created during the prepare step. This file will be later parsed in the
    execution step. The `barista-execution-context` file should be a toml file
    containing at least one of the following fields:
        - `app-args`
        - `vm-options`

      with a string value assigned. An example of the `barista-execution-context` file:
      ```
      generated = 2024-11-19 14:22:27
      vm-options = "-Dopt1=val1 -Dopt2=val2 -Dopt3=val3"
      ```
      Where:
        - `generated`:
            - is assigned a timestamp taken at the moment of file creation
            - this field is ignored by the harness
        - `vm-options`:
            - is assigned a string value containing all of the VM options that
            should be propagated to the app during the execution step
            - these options are concatenated to the VM options specified in the
            CLI/config file
- (OPTIONAL) contain a `cleanup.sh` script
    - is intended to ensure the system is left in the same state it was
    in before benchmarking. All the resources acquired during the prepare step
    should be released (e.g. the auxilliary services should be stopped, the
    `barista-execution-context` file should be deleted).
