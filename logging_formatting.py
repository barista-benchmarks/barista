import re
import logging as log


def log_startup(results):
    """Logs startup response times.

    :param list results: List containing startup response times.
    """
    for datapoint in results:
        iteration = datapoint["iteration"]
        response_time = datapoint["response_time"]
        log_aligned_datapoint(f"response #{iteration + 1:02}", f"{response_time:.2f}", "ms")

def log_throughput(measurement_map, iteration_number=None):
    """Logs the results of measured throughput.

    :param dict measurement_map: Dictionary containing throughput measurement information.
    :param number iteration_number: Number of the iteration in which the measurements were recorded.
    """
    if iteration_number is not None:
        log.info(f"\tMeasures for throughput iteration {iteration_number}:")
    else:
        log.info("\tMeasures for throughput:")
    for metric, value in measurement_map.items():
        # Omit all fields but the recorded metric to make the stdout more readable
        if metric in ["command", "iteration", "script"]:
            continue
        log_aligned_datapoint(metric, f"{value:.2f}", "ops/s")

def log_latency(latency_result, iteration_number=None):
    """Logs the results of measured latencies.

    :param dict latency_result: Dictionary containing latency measurement information.
    :param number iteration_number: Number of the iteration in which the measurements were recorded.
    """
    if iteration_number is not None:
        log.info(f"\tMeasures for latency iteration {iteration_number}:")
    log_aligned_datapoint("rate", latency_result['rate'], "ops/s")
    if 'meets_sla' in latency_result:
        log_aligned_datapoint("Met SLA", latency_result['meets_sla'], "")
    for percentile, score in latency_result['p_values'].items():
        log_aligned_datapoint(f"{percentile:.3f}", f"{score:.2f}", "ms")

def log_memory_usage(p_values):
    """Logs the app process' memory usage.

    :param dict p_values: Dictionary containing memory usage percentile values.
    """
    for percentile, score in p_values.items():
        log_aligned_datapoint(percentile, f"{score:.2f}", "MB")

def log_cpu_percent(p_values):
    """Logs the app process' cpu usage.

    :param dict p_values: Dictionary containing cpu usage percentile values.
    """
    for percentile, score in p_values.items():
        log_aligned_datapoint(percentile, f"{score:.2f}", "%")

def log_aligned_datapoint(name, value, unit):
    """Provides a standardized alignment for logging a single datapoint.

    Use this function to ensure all the datapoints are aligned.

    :param str name: Datapoint name.
    :param str value: Datapoint value.
    :param str unit: Datapoint measurement unit.
    """
    log.info(f"\t\t{name:>20} {value:>20} {unit}")