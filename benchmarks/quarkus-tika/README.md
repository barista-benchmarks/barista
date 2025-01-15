# Quarkus Tika Benchmark

Tika is a Quarkus PDF/ODT processing application.

This code is based on commit id `d76944df26f03ff383a74a04fe5a1543723c7918` from the Quarkus [Tika quickstart](https://github.com/quarkusio/quarkus-quickstarts/tree/d76944df26f03ff383a74a04fe5a1543723c7918/tika-quickstart).

## Building:

Build the app: `./mvnw package`

## Building a native-image:

To build the native-image: `./mvnw package -Pnative`

## Benchmarking:

Benchmarking with Tika is currently supported with `mx`. There are two benchmarking tools available:

- Wrk (used to measure throughput)
- Wrk2 (used to measure latency).

For each benchmarking tool, one or more workloads are available (check `workloads` directory).

To start the benchmark, simply use `mx benchmark` followed by the benchmark name (`tika-wrk`) and the workload. As an example, the two following lines use the same benchmark and workload in two different JVMs (`server` and `native-image`).

- `mx benchmark tika-wrk:pdf-tiny -- --jvm=server`
- `mx benchmark tika-wrk:pdf-tiny -- --jvm=native-image`
