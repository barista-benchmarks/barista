from configuration import LatencyMode
from wrk2_load_generator import Wrk2LoadGenerator
import re
import copy
import logging as log
import os

MEETS_SLA = 'meets_sla'
FIXED_PERCENTAGE = 'FIXED_PERCENTAGE'

class ThroughputExplorer():

    def __init__(self, latency_config, output_dir, endpoint, throughput_result, env):
        self._latency_config = latency_config
        self._throughput = throughput_result
        self._output_dir = output_dir
        self._endpoint = endpoint
        self._counter = 0
        self._env = env

        self.find_avg_throughput()

    def explore(self):
        if self._latency_config.search_strategy == LatencyMode.FIXED:
            # Corner case when we dont want to find optimal rate
            if self._latency_config.iteration_count <=0:
                return {}
            measurements = self.get_fixed_rates()
        elif self._latency_config.search_strategy == LatencyMode.BINARY_SEARCH:
            measurements = self.get_binary_search_rate()
        elif self._latency_config.search_strategy == LatencyMode.AIMD:
            measurements = self.get_aimd_rate()
        else:
            raise ValueError(f"Could not determine search strategy {self._latency_config.search_strategy.name}")

        latency_results = []

        for script in self._latency_config.script if self._latency_config.script is not None else [None]:
            for search_strategy, identified_opt_rates in measurements['to_measure'].items():
                for rate in identified_opt_rates:
                    latency_results += self.measure_and_dump(script, rate, search_strategy)

        res = {}
        res['final_measurements'] = latency_results
        if 'performed_measurements' in measurements:
            res.update(measurements['performed_measurements'])
        return res

    def measure_and_dump(self, script, rate, mode_name):
        measure_rate = rate
        name = rate
        if mode_name == FIXED_PERCENTAGE:
            measure_rate = rate[0]
            name = rate[1]
        latency_load_gen = Wrk2LoadGenerator(self._latency_config, self._output_dir, self._endpoint, self._env)
        log.info(f"Now measuring the latency for {mode_name} mode at {measure_rate} for {self._latency_config.iteration_count} iterations")

        latency_results = []
        for i in range (self._latency_config.iteration_count):
            log.info(f"Running latency iteration {i+1}/{self._latency_config.iteration_count}")
            latency_result_map = latency_load_gen.measure(measure_rate, self._latency_config.iteration_duration, script)
            measurement_dict = {
                    "rate": measure_rate,
                    "p_values": latency_result_map['p_values'],
                    "command": latency_result_map["command"]
                    }
            
            if self._latency_config.sla_requirement is not None:
                measurement_dict['meets_sla'] = self.meets_sla(latency_result_map['p_values'], measure_rate)
            
            if mode_name == FIXED_PERCENTAGE:
                measurement_dict['percentage'] = rate[1]
            measurement_dict['iteration'] = i
            if script is not None:
                measurement_dict['script'] = os.path.basename(script)
            latency_results.append(measurement_dict)
            latency_load_gen.dump_stdout(self._output_dir, latency_result_map['stdout'], f"{mode_name}-{name}-latency-{i+1}")
        return latency_results
        
    def determine_rate(self):
        if self._latency_config.mode == LatencyMode.FIXED:
            return self.get_fixed_rates()
        elif self._latency_config.mode == LatencyMode.BINARY_SEARCH:
            return self.get_binary_search_rate()
        elif self._latency_config.mode == LatencyMode.AIMD:
            return self.get_aimd_rate()


    def find_avg_throughput(self):
        """
        Finds maximum average throughput
        """
        sum_of_throughputs = 0
        for measurements in self._throughput:
            sum_of_throughputs += measurements['throughput']
        self._avg = sum_of_throughputs/len(self._throughput) if len(self._throughput) > 0 else 0
        if (self._avg < 1):
            log.warning(f"Average throughput was: {self._avg} ops/s. Setting average throughput to 1")
            self._avg = 1
        log.info(f"Average throughput: {self._avg} ops/s")
    
    def get_fixed_rates(self):
        """
        Returns all the requested fixed rates in a map
        """
        log.info("Getting fixed rates for latency")
        res = {}
        if self._latency_config.percentages is not None:
            res[FIXED_PERCENTAGE] = []
            for percentage in self._latency_config.percentages:
                res[FIXED_PERCENTAGE].append([int(percentage * self._avg), percentage * 100])
        if self._latency_config.rates is not None:
            res['FIXED'] = []
            for rate in self._latency_config.rates:
                res['FIXED'].append(rate)
        
        return {"to_measure": res}

    def get_binary_search_rate(self):
        log.info("Performing binary search for maximal throughput that doesn't breach the SLA")
        min_bound = 0.0
        max_bound = 1.0
        accuracy = self._latency_config.base_step

        measurements = []

        while (min_bound + accuracy) < max_bound:
            mid_rate_percentage = (min_bound + max_bound) / 2
            single_measurement = self.measure_once(mid_rate_percentage)
            is_in_bounds = self.check_bounds_and_sla(single_measurement, mid_rate_percentage)
            result = {}
            result['p_values'] = single_measurement['p_values']
            result['meets_sla'] = is_in_bounds
            result['rate'] = mid_rate_percentage * self._avg
            measurements.append(result)

            if is_in_bounds:
                min_bound = mid_rate_percentage
            else :
                max_bound = mid_rate_percentage
        log.info(f"Binary search found rate of {int(min_bound * self._avg)}")
        return {"to_measure": {"BINARY_SEARCH": [int(min_bound * self._avg)]},
                "performed_measurements": {"BINARY_SEARCH": measurements}}

    def get_aimd_rate(self):
        """
        Performs search on the microservice to find maximum throughput not breaching the SLA.
        Uses Additive Increase/ Multiplicative Decrease (AIMD) with exponential increase of multiplier 2
        """
        log.info("Performing exponential Additive Increase/ Multiplicative Decrease(exponential) to find peak throughput with optimal latency")
        max_multiplier = 1
        min_multiplier = 0.00
        #Range (0,1]
        base_step = self._latency_config.base_step

        current_step = base_step

        current_rate_multiplier = min_multiplier + current_step
        step_count = 0
        times_reset = 0

        #Create a copy with smaller duration for performing tests
        measurements = []

        while True:
            current_rate_multiplier = min_multiplier + current_step*(2**step_count)
            log.info(f"Current AIMD multiplier: {current_rate_multiplier} ")
            current_rate = current_rate_multiplier
            res = self.measure_once(current_rate)
            is_in_bounds = self.check_bounds_and_sla(res, current_rate)
            result = {}
            result['p_values'] = res['p_values']
            result['meets_sla'] = is_in_bounds
            result['rate'] = current_rate * self._avg
            measurements.append(result)

            step_count += 1
            next_rate = min_multiplier + current_step * (2**step_count)

            if not is_in_bounds:
                max_multiplier = current_rate_multiplier
                min_multiplier = min_multiplier + current_step*(2**(step_count-2))
                step_count = 0
                times_reset +=1
            elif next_rate > max_multiplier :
                min_multiplier = current_rate_multiplier
                #reset
                step_count = 0
                times_reset += 1
            if times_reset > 2:
                break
            current_step = base_step * (max_multiplier-min_multiplier)
        log.info(f"Performed adjustments {times_reset} times. Settled for {min_multiplier} multiplier. Optimal rate: {min_multiplier * self._avg} op/s")
        return {"to_measure" : {"AIMD": [int(min_multiplier * self._avg)]},
                "performed_measurements": {"AIMD": measurements}}

    def get_measured_throughput(self, output):
        matches = re.findall(r"^Requests/sec:\s*(?P<throughput>\d*[.,]?\d*)\s*$", output, re.MULTILINE)
        if len(matches) != 1:
            raise ValueError(f"Expected exactly 1 match for throughput value in {output}")
        
        return float(matches[0])

    def meets_sla(self, measured_pvalues, rate):
        met_all_sla = True
        for percentile, latency in self._latency_config.sla_requirement.items():
            measured = measured_pvalues[percentile]
            if latency <= measured:
                log.info(f"Percentile {percentile} has breached SLA. Required: {latency}ms, measured: {measured}ms")
                met_all_sla = False
            else:
                log.info(f"Successfully met SLA for percentile {percentile}! Latency is < {latency}ms. Measured {measured}ms at {rate} op/s")
        if met_all_sla:
            log.info("Met all SLA requirements")
        return met_all_sla


    def measure_once(self, expected_rate_percentage):
        measurment_duration_s = 30
        log.info(f"Performing short measurement of {measurment_duration_s}s for determining next optimal rate")
        request_rate = int(expected_rate_percentage * self._avg)

        latency_benchmark = Wrk2LoadGenerator(self._latency_config, self._output_dir, self._endpoint, self._env)
        results = latency_benchmark.measure(request_rate, measurment_duration_s)
        latency_benchmark.dump_stdout(self._output_dir, results['stdout'], f"latency-adjustment-{self._counter+1}")
        self._counter += 1
        return results

    def check_bounds_and_sla(self, results, expected_rate_percentage):
        rate = expected_rate_percentage * self._avg
        actual_throughput = self.get_measured_throughput(results['stdout'])
        log.info(f"Reported throughtput {actual_throughput}. Expected throughput {rate}")
        meets_sla = True
        if self._latency_config.sla_requirement is not None:
            log.info(f"Checking if {rate} meets the SLA requirements")
            meets_sla = self.meets_sla(results['p_values'], rate)

        return (abs(rate - actual_throughput) <= (rate)) and meets_sla