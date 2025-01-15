# Quarkus Hello World Benchmark

This benchmark exposes a simple `/hello` GET endpoint that returns `Hello, World!`.
The code in this benchmark is based on commit id `d76944df26f03ff383a74a04fe5a1543723c7918` from the Quarkus [getting started quickstart](https://github.com/quarkusio/quarkus-quickstarts/tree/d76944df26f03ff383a74a04fe5a1543723c7918/getting-started)

# Building The Benchmark

To build the benchmark, run: `mvn package`

# Building The Native-Image

To build the native-image of the benchmark, run: `mvn -Pnative package`

## Benchmarking:

Benchmarking is currently supported with `mx`. There are two benchmarking tools available:

- Wrk (used to measure throughput)
- Wrk2 (used to measure latency).

For each benchmarking tool, one or more workloads are available (check `workloads` directory).

To start the benchmark, simply use `mx benchmark` followed by the benchmark name (`helloworld`), followed by the workloads. As an example, the two following lines use the same benchmark and workload in two different JVMs (`server` and `native-image`).

- `mx benchmark quarkus-helloworld-wrk:helloworld -- --jvm=server`
- `mx benchmark quarkus-helloworld-wrk:helloworld -- --jvm=native-image`
