import pandas as pd
import os
import glob
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

from tools.statistics_stops import StatisticsStops

from seqscan.data.trajectory import Trajectory
from seqscan.data.point import Point
from seqscan.data.stop_point import Stop_Point
from seqscan.seqscan import SeqScan

from datetime import datetime

import json

with open('.\config.json') as f:
    config = json.load(f)

# Access global variables
TIMESTAMP_FORMAT = config["TIMESTAMP_FORMAT"]

TAG_COLUMN=config["CSV_columns"]["TAG_COLUMN"]
TIME_COLUMN=config["CSV_columns"]["TIME_COLUMN"]
X_COLUMN=config["CSV_columns"]["X_COLUMN"]
Y_COLUMN=config["CSV_columns"]["Y_COLUMN"]

CLASS_COLUMN=config["OUTPUT_COLUMNS"]["CLASS"]
TYPE_COLUMN=config["OUTPUT_COLUMNS"]["TYPE"]
DETAILS_COLUMN=config["OUTPUT_COLUMNS"]["DETAILS"]



class RunStopsStatistics():


    def read_single_stop_points_from_file(self, input_file):
        stop_points = []
        df = pd.read_csv(input_file)
        if TAG_COLUMN in df.columns:
            for _, row in df.iterrows():
                stop_point = Stop_Point(row[X_COLUMN], row[Y_COLUMN], row[TIME_COLUMN], row[CLASS_COLUMN],
                                        row[TYPE_COLUMN], row[DETAILS_COLUMN], row[TAG_COLUMN])
                stop_points.append(stop_point)
        else:
            for _, row in df.iterrows():
                stop_point = Stop_Point(row[X_COLUMN], row[Y_COLUMN], row[TIME_COLUMN], row[CLASS_COLUMN],
                                        row[TYPE_COLUMN], row[DETAILS_COLUMN])
                stop_points.append(stop_point)
        return stop_points

    def read_multiple_stop_points_from_file(self, input_file):
        stop_points_dict = {}
        df = pd.read_csv(input_file)
        if TAG_COLUMN in df.columns:
            for _, row in df.iterrows():
                if row[TAG_COLUMN] not in stop_points_dict:
                    stop_points_dict[row[TAG_COLUMN]] = []
                stop_point = Stop_Point(row[X_COLUMN], row[Y_COLUMN], row[TIME_COLUMN], row[CLASS_COLUMN],
                                        row[TYPE_COLUMN], row[DETAILS_COLUMN], row[TAG_COLUMN])
                stop_points_dict[row[TAG_COLUMN]].append(stop_point)

        return stop_points_dict


    def process_single_file_from_folder(self, f):
        f_output = os.path.basename(f)
        self.run_statistics_single_mode(f, self.output_folder + 'output_' + f_output)
        del f_output

    def process_one_trajectory_of_multi(self, traj):
        tag_id=traj[0].tag_id
        stats = StatisticsStops(traj, self.output_file,tag_id=tag_id, multi_mode=2)
        stats.run()
        del stats

    def run_statistics_single_mode(self,  input_path_f, output_path):
        trajectory= self.read_single_stop_points_from_file(input_path_f)
        tag_id = trajectory[0].tag_id
        stats = StatisticsStops(trajectory, output_path,tag_id=tag_id,  multi_mode=0)
        results=stats.run()
        #results.stamp()
        del stats

    def run_statistics_multi_mode(self, input_folder=None, output_folder=None, input_file=None, output_file=None, max_processors=1):

        if input_file is None and input_folder is None:
            print('Please specify if input_file or input_folder')
            return
        elif input_file is not None and input_folder is not None:
            print('Please specify if input_file or input_folder, specifying both will create confusion')
            return
        elif input_file is not None and output_file is None:
            print('Please specify the output_file')
            return
        elif input_folder is not None and output_folder is None:
            print('Please specify the output_folder')
            return

        processors_available = multiprocessing.cpu_count()

        if max_processors > 1 and max_processors > processors_available:
            print("maximum number of processors available on your machine is: ", processors_available, ""
                                                                                                       ". This number will be used instead of ",
                  max_processors)
            max_processors = processors_available

        self.max_processors=max_processors

        if max_processors>1:
            self.parallelism=True
        else:
            self.parallelism=False

        if input_file is not None:
            self.output_file=output_file
            dict_list= self.read_multiple_stop_points_from_file(input_file)
            distinct_traj=list(dict_list.keys())
            trajectory1=dict_list[distinct_traj[0]]
            stats = StatisticsStops(trajectory1, output_file, tag_id=distinct_traj[0], multi_mode=1)
            stats.run()
            remaining_trajectories=[value for key, value in dict_list.items() if key != distinct_traj[0]]

            if self.parallelism:
                with ProcessPoolExecutor(max_workers=self.max_processors) as ex:
                    res = ex.map(self.process_one_trajectory_of_multi, remaining_trajectories)
                return list(res)
            else:
                for traj in remaining_trajectories:
                    self.process_one_trajectory_of_multi(traj)


        elif input_folder is not None:
            self.output_folder=output_folder
            csv_input_files = glob.glob(os.path.join(input_folder, "*.csv"))

            if self.parallelism:
                with ProcessPoolExecutor(max_workers=self.max_processors) as ex:
                    res = ex.map(self.process_single_file_from_folder, csv_input_files)
                return list(res)
            else:
                for f in csv_input_files:
                    self.process_single_file_from_folder(f)




if __name__ == '__main__':

    stops_stats = RunStopsStatistics()

    # The input is a point classifications file obtained as a result of SeqScan
    #input_path_f = "./output/seqscan_atc_7traj.csv"
    # The output is a file containing the statistics over stops for every trajectory
    #output_path_f = "./output/stats_seqscan_atc_7traj.csv"

    # Run the statistics using the bulk mode
    #stops_stats.run_statistics_multi_mode(input_file=input_path_f,
    #                            output_file=output_path_f)







