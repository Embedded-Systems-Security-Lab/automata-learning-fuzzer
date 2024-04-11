import csv
import json
from FMI.utils import constants

class CoverageReport(object):

    @staticmethod
    def prepare_csv(file_path, header):
        with open(file_path, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=header)
            writer.writeheader()

    @staticmethod
    def update_file(file_path, data: list):
        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=constants.HEADER)
            writer.writerows(data)
            f.flush()

    @staticmethod
    def write_run_parameters(json_file, data):
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
            f.flush()
