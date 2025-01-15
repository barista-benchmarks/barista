from abstract_load_generator import AbstractLoadGenerator
import re
import logging as log

class AbstractWrkLoadGenerator(AbstractLoadGenerator):
    def load_parser(self, measurement):
        latency_measures = re.findall("\s\s\s\sLatency\s*([0-9]*.[0-9]*[a-z]*)\s*([0-9]*.[0-9]*[a-z]*)\s*([0-9]*.[0-9]*[a-z]*)\s*([0-9]*.[0-9]*[a-z]*%)", measurement)
        reqs = re.findall("Requests\/sec: +(\d+\.?\d*\w*)", measurement)
        if len(latency_measures) != 1 or len(reqs) != 1:
            raise ValueError("Measurements not found")
        
        return {
            "latency":{
            "AVG": latency_measures[0][0],
            "Stdev": latency_measures[0][1],
            "MAX": latency_measures[0][2],
            "+- Stdev": latency_measures[0][3]
            }, 
        "throughput" :{
            "throughput" : self.throughput_to_unit(reqs[0]),
            }
        }

    def throughput_to_unit(self, str_number):
        number, unit = re.findall(r"(\d+\.?\d*)(\w*)", str_number)[0]
        if unit == 'k':
            return float(number) * (10**3)
        elif unit == 'M':
            return float(number) * (10**6)
        elif unit == 'G':
            return float(number) * (10**9)
        elif unit == 'T':
            return float(number) * (10**12)
        elif unit == 'P':
            return float(number) * (10**15)
        else:
            return float(number)

    def dump_stdout(self, output_foler, output, name):
        output_file = f"{output_foler}/{name}-dump.txt"
        log.info(f"Dumping wrk outputs to file '{output_file}' and to stdout:\n{output}")
        with open (output_file, "w") as file:
            file.write(output)
    
    def crash_dump(self, output_foler, output):
        output_file = f"{output_foler}/crash-dump.txt"
        log.error(f"{self.__class__.__name__} crashed! Dumping crashed wrk outputs to {output_file} and also logging them:\n{output}")
        with open (output_file, "w") as file:
            file.write(output)