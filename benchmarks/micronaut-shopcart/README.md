# Micronaut ShopCart Benchmark

ShopCart is a Micronaut web shopping application.

# Building The Benchmark

To build the benchmark, run: `mvn package`

# Building The Native-Image

To build the native-image of the benchmark, run: `mvn package -Dpackaging=native-image`

## Benchmarking:

Benchmarking with ShopCart is currently supported with `mx`. There are three benchmarking tools available:

- JMeter (used to measure throughput)
- Wrk (used to measure throughput)
- Wrk2 (used to measure latency).

For each benchmarking tool, one or more workloads are available (check `workloads` directory).

To start the benchmark, simply use `mx benchmark` followed by the benchmark name (`shopcart-jmeter`, `shopcart-wrk`), followed by the workloads. As an example, the two following lines use the same benchmark and workload in two different JVMs (`server` and `native-image`).

- `mx benchmark shopcart-wrk:mixed-tiny -- --jvm=server`
- `mx benchmark shopcart-wrk:mixed-tiny -- --jvm=native-image`
