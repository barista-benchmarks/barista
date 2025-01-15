import csv
import json
import logging as log
import re
import os
from configuration import P_VALUES_MAP

STARTUP_RESULTS_FILE = "barista_startup_results.csv"
WARMUP_RESULTS_FILE = "barista_warmup_results.csv"
THROUGHPUT_RESULTS_FILE = "barista_throughput_results.csv"
LATENCY_RESULTS_FILE = "barista_latency_results.csv"
RESOURCE_MEASUREMENTS_FILE = "barista_resource_usage.csv"
GENERAL_RESULTS_JSON_FILE = "barista-results.json"

RSS_PERCENTILES = [100, 99, 98, 97, 96, 95, 90, 75, 50, 25]
VMS_PERCENTILES = [100, 99, 98, 97, 96, 95, 90, 75, 50, 25]
CPU_PERCENTILES = [100, 99, 98, 97, 96, 95, 90, 75, 50, 25]

def compile_usage_p_values(usage_data):
    """Compiles percentile values for the resource usage metrics recorded during the benchmark.

    The metrics recorded are:
     * 'rss' - Resident Set Size
     * 'vms' - Virtual Memory Size
     * 'cpu' - system-wide CPU utilization as a percentage

    :param list usage_data: Raw values for 'rss', 'vms' and 'cpu' recorded during the benchmark.
    :return: Percentile values for 'rss', 'vms' and 'cpu'.
    :rtype: (dict, dict, dict)
    """
    if not usage_data:
        raise ValueError("No resource usage data!")

    rss_values = [datapoint[1] for datapoint in usage_data]
    vms_values = [datapoint[2] for datapoint in usage_data]
    cpu_values = [datapoint[3] for datapoint in usage_data]

    rss_p_values = compile_p_values(rss_values, RSS_PERCENTILES)
    rss_p_values = {percentile: p_value / (1024 * 1024) for percentile, p_value in rss_p_values.items()} # cast from bytes to megabytes
    vms_p_values = compile_p_values(vms_values, VMS_PERCENTILES)
    vms_p_values = {percentile: p_value / (1024 * 1024) for percentile, p_value in vms_p_values.items()} # cast from bytes to megabytes
    cpu_p_values = compile_p_values(cpu_values, CPU_PERCENTILES)

    return rss_p_values, vms_p_values, cpu_p_values

def compile_p_values(values, percentiles):
    """Compiles percentile values from raw values.

    :param list values: The raw values.
    :param list percentiles: The percentiles for which percentile values are to be compiled.
    :return: Percentile values.
    :rtype: list
    """
    sorted_values = sorted(values)

    def pc(k): # k-percentile with linear interpolation between closest ranks
        x = (len(sorted_values) - 1) * float(k) / 100
        fr = int(x)
        cl = int(x + 0.5)
        v = sorted_values[fr] if fr == cl else sorted_values[fr] * (cl - x) + sorted_values[cl] * (x - fr)
        return v

    p_values = {f"p{float(percentile)}": pc(percentile) for percentile in percentiles}
    return p_values

def usage_to_csv(directory, resources):
    """Writes the resource usage recorded during the benchmark into a csv file.

    :param list resources: Resource usage recorded during the benchmark.
    """
    csv_file_path = os.path.abspath(os.path.join(directory, RESOURCE_MEASUREMENTS_FILE))
    with open(csv_file_path, 'w', newline='\n') as file:
        writer = csv.writer(file)

        writer.writerow(['time','rss_mb','vms_mb', 'cpu'])
        for time, rss, vms, cpu in resources:
            # cast rss and vms from bytes to megabytes
            writer.writerow([time, rss / (1024 * 1024), vms / (1024 * 1024), cpu])

def results_to_csv(directory, results):
    """Writes the results of each phase of the benchmark into separate csv files.

    :param dict results: All of the data gathered by the Barista harness.
    """
    log.info("Writing to csv files")
    if results['startup'] and results['startup']['measurements']:
        startup_to_csv(directory, results['startup']['measurements'])
    else:
        log.debug(f"No startup data - not producing a startup results file")
    if results['warmup'] and results['warmup']['measurements']:
        warmup_to_csv(directory, results['warmup'])
    else:
        log.debug(f"No warmup data - not producing a warmup results file")
    if results['throughput'] and results['throughput']['measurements']:
        throughput_to_csv(directory, results['throughput'])
    else:
        log.debug(f"No throughput data - not producing a throughput results file")
    if results['latency']:
        latency_to_csv(directory, results['latency'])
    else:
        log.debug(f"No latency data - not producing a latency results file")
    if results['resource_usage'] and results['resource_usage']['raw']:
        usage_to_csv(directory, results['resource_usage']['raw'])

def startup_to_csv(directory, startup_result):
    """Writes the results of the startup phase of the benchmark into a csv file.

    :param list startup_result: Results of the startup phase of the benchmark.
    """
    if not startup_result:
        raise ValueError("No startup data!")

    log.info(f"Producing {STARTUP_RESULTS_FILE}")
    csv_file_path = os.path.abspath(os.path.join(directory, STARTUP_RESULTS_FILE))
    with open(csv_file_path, "w", newline="\n") as file:
        writer = csv.writer(file)

        writer.writerow(["iteration", "response_time"])
        for startup_record in startup_result:
            writer.writerow([startup_record["iteration"], startup_record["response_time"]])

def warmup_to_csv(directory, warmup_result):
    """Writes the results of the warmup phase of the benchmark into a csv file.

    :param dict warmup_result: Results of the warmup phase of the benchmark.
    """
    if not warmup_result:
        raise ValueError("No warmup data!")

    log.info(f"Producing {WARMUP_RESULTS_FILE}")
    csv_file_path = os.path.abspath(os.path.join(directory, WARMUP_RESULTS_FILE))
    with open(csv_file_path, 'w', newline='\n') as file:
        writer = csv.writer(file)

        writer.writerow(['iteration', 'throughput'])
        for i in range(len(warmup_result['measurements'])):
            name = str(i)
            writer.writerow([name, warmup_result['measurements'][i]['throughput']])

def throughput_to_csv(directory, throughput_result):
    """Writes the results of the throughput phase of the benchmark into a csv file.

    :param dict throughput_result: Results of the throughput phase of the benchmark.
    """
    if not throughput_result:
        raise ValueError("No throughput data!")

    log.info(f"Producing {THROUGHPUT_RESULTS_FILE}")
    csv_file_path = os.path.abspath(os.path.join(directory, THROUGHPUT_RESULTS_FILE))
    with open(csv_file_path, 'w', newline='\n') as file:
        writer = csv.writer(file)

        writer.writerow(['iteration', 'throughput'])
        for i in range(len(throughput_result['measurements'])):
            name = str(i)
            writer.writerow([name, throughput_result['measurements'][i]['throughput']])

def latency_to_csv(directory, latency_result):
    """Writes the results of the latency phase of the benchmark into a csv file.

    :param dict latency_result: Results of the latency phase of the benchmark.
    """
    if not latency_result:
        raise ValueError("No latency data!")

    for name, measurements in latency_result['measurements'].items():
        log.info(f'Producing {name}-{LATENCY_RESULTS_FILE}')
        csv_file_path = os.path.abspath(os.path.join(directory, f"{name}-{LATENCY_RESULTS_FILE}"))
        with open(csv_file_path, 'w', newline='\n') as file:
            writer = csv.writer(file)

            writer.writerow(["script", "iteration", "request_rate", "percentile", "latency"])
            for measurement in measurements:
                script = measurement.get("script")
                iteration = measurement["iteration"]
                request_rate = measurement["rate"]
                p_values = measurement["p_values"]
                for percentile, latency in p_values.items():
                    writer.writerow([script, iteration, request_rate, percentile, latency])

def dump_result_json(directory, result):
    """Saves the benchmark results to a JSON file.

    :param dict result: All of the data gathered by the Barista harness.
    """
    json_file = os.path.abspath(os.path.join(directory, GENERAL_RESULTS_JSON_FILE))
    log.info(f"Saving all collected metrics to JSON file: {json_file}")
    with open (json_file, "w") as f:
        json.dump(result, f, indent=4)