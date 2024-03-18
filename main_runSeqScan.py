import pandas as pd
import os
import glob
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

from seqscan.data.trajectory import Trajectory
from seqscan.data.point import Point
from seqscan.seqscan import SeqScan

from datetime import datetime

import json

with open('.\config.json') as f:
    config = json.load(f)

# Access global variables
TIMESTAMP_FORMAT = config["TIMESTAMP_FORMAT"]

TAG_COLUMN = config["CSV_columns"]["TAG_COLUMN"]
TIME_COLUMN = config["CSV_columns"]["TIME_COLUMN"]
X_COLUMN = config["CSV_columns"]["X_COLUMN"]
Y_COLUMN = config["CSV_columns"]["Y_COLUMN"]

TIME_UNIT = config["UNITS"]["TIME"]


class mainRun():

    def read_multi_traj_from_csv(self, path):
        col_list = [TAG_COLUMN, X_COLUMN, Y_COLUMN, TIME_COLUMN]
        df = pd.read_csv(path, usecols=col_list)[col_list]
        df.sort_values(by=[TAG_COLUMN, TIME_COLUMN])
        data_list = df.values.tolist()
        points_list = list()
        self.list_trajectories = list()

        tag1 = data_list[0][0]
        for l in data_list:
            # print(l)
            if l[0] == tag1:
                p = Point(l[1], l[2], datetime.strptime(l[3], TIMESTAMP_FORMAT))
                points_list.append(p)

            else:
                trajectory = Trajectory(points_list, tag_id=tag1)
                self.list_trajectories.append(trajectory)
                tag1 = l[0]
                points_list = list()
                p = Point(l[1], l[2], datetime.strptime(l[3], TIMESTAMP_FORMAT))
                points_list.append(p)

        trajectory = Trajectory(points_list, tag_id=tag1)
        self.list_trajectories.append(trajectory)

    def read_single_traj_from_csv(self, path):
        tag_id=None
        col_list = [X_COLUMN, Y_COLUMN, TIME_COLUMN]
        df = pd.read_csv(path)#, usecols=col_list)
        if TAG_COLUMN in df.columns:
            tag_id=df[TAG_COLUMN].iloc[0]

        df = pd.read_csv(path , usecols=col_list)[col_list]
        df.sort_values(by=[TIME_COLUMN])
        data_list = df.values.tolist()
        points_list = list()
        # self.list_trajectories=list()

        for l in data_list:
            p = Point(l[0], l[1], datetime.strptime(l[2], TIMESTAMP_FORMAT))
            points_list.append(p)

        trajectory = Trajectory(points_list, tag_id=tag_id)
        # self.list_trajectories.append(trajectory)
        return trajectory

    def process_single_file(self, f):
        print('ok')
        f_output = os.path.basename(f)
        out_classification = self.output_folder + 'output_' + f_output
        out_symbolic = self.output_folder_symbolic + 'output_symbolic' + f_output
        self.run_ss_single_mode(self.eps, self.delta, self.n, f, out_classification, out_symbolic)
        del f_output

    def run_ss_single_mode(self, eps, delta, n, input_path_f, output_path, output_path_symbolic):
        directory = os.path.dirname(output_path)
        # Create directories if they do not exist
        os.makedirs(directory, exist_ok=True)
        directory = os.path.dirname(output_path_symbolic)
        os.makedirs(directory, exist_ok=True)

        trajectory = self.read_single_traj_from_csv(input_path_f)
        seqscan = SeqScan(trajectory, output_path, output_path_symbolic, silent=False, multi_mode=0)
        seqscan.run(eps, n, self.convert_time_to_s(delta))
        del seqscan

    def process_one_trajectory_of_multi(self, traj):
        seqscan = SeqScan(traj, self.output_file, self.output_file_symbolic, silent=False, multi_mode=2)
        seqscan.run(self.eps, self.n, self.convert_time_to_s(self.delta))
        del seqscan

    def run_ss_multi_mode(self, eps, delta, n, input_folder=None, output_folder=None, input_file=None, output_file=None,
                          max_processors=1):
        self.eps = eps
        self.delta = delta
        self.n = n

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

        self.max_processors = max_processors

        if max_processors > 1:
            self.parallelism = True
        else:
            self.parallelism = False

        if input_file is not None:
            self.output_file = output_file

            file_name = "symbolic_" + os.path.basename(output_file)
            directory = os.path.dirname(output_file)
            self.output_file_symbolic = os.path.join(directory, file_name)

            self.read_multi_traj_from_csv(input_file)
            trajectory1 = self.list_trajectories[0]
            seqscan = SeqScan(trajectory1, self.output_file, self.output_file_symbolic, silent=False, multi_mode=1)
            seqscan.run(eps, n, self.convert_time_to_s(delta))
            print(trajectory1.tag_id, ' is done')

            if self.parallelism:
                with ProcessPoolExecutor(max_workers=self.max_processors) as ex:
                    res = ex.map(self.process_one_trajectory_of_multi, self.list_trajectories[1:])
                return list(res)
            else:
                for traj in self.list_trajectories[1:]:
                    self.process_one_trajectory_of_multi(traj)
                    print(traj.tag_id, ' is done')


        elif input_folder is not None:
            self.output_folder = output_folder
            self.output_folder_symbolic = output_folder + '/symbolic/'
            csv_input_files = glob.glob(os.path.join(input_folder, "*.csv"))

            if self.parallelism:
                with ProcessPoolExecutor(max_workers=self.max_processors) as ex:
                    res = ex.map(self.process_single_file, csv_input_files)
                return list(res)
            else:
                for f in csv_input_files:
                    self.process_single_file(f)


    def convert_time_to_s(self, delta):
        unit=TIME_UNIT
        if unit=="min":
            return delta*60
        if unit=="d":
            return delta*3600*24
        return delta




if __name__ == '__main__':
    seqscan = mainRun()

    #input_path_f = "./input/atc_7traj.csv"
    #output_path_f = "./output/seqscan_atc_7traj.csv"
    #seqscan.run_ss_multi_mode(1000, 10, 5, input_file=input_path_f, output_file=output_path_f, max_processors=3)

    ## The input is a folder of 7 separate csv files
    #input_path_folder = "./input/atc_7traj/"
    ## The output path is for a folder where the points classification files
    ## are going to be saved, and the folder of symbolic trajectories too
    #output_path_folder = "./output/seqscan_output/"

    ## Run Seqscan, using bulk mode, with 10 processors in parallel
    #seqscan.run_ss_multi_mode(1000, 10, 5,  # Seqscan parameters
    #                          input_folder=input_path_folder,
    #                          output_folder=output_path_folder,
    #                          max_processors=10)

    #input_path_f = "./input/geolife_example.csv"
    #output_path_f = "./output/seqscan_geolife_example.csv"
    #output_path_f_symbolic = "./output/symbolic_seqscan_geolife_example.csv"
    #8 m, 15 minutes, 30 points
    #seqscan.run_ss_single_mode(8, 15, 30, input_path_f, output_path_f, output_path_f_symbolic)
