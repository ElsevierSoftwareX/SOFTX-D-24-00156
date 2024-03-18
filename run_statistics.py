import pandas as pd
import os
import glob
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

from tools.statistics_trajectories import StatisticsTrajectories


from seqscan.data.trajectory import Trajectory
from seqscan.data.point import Point
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



class RunStatistics():


    def read_multi_traj_from_csv(self, path):
        col_list = [TAG_COLUMN, X_COLUMN, Y_COLUMN, TIME_COLUMN ]
        df = pd.read_csv(path, usecols=col_list)[col_list]
        data_list= df.values.tolist()
        points_list=list()
        self.list_trajectories=list()

        tag1=data_list[0][0]
        for l in data_list:
            if l[0]==tag1:
                p=Point(l[1], l[2], datetime.strptime(l[3],TIMESTAMP_FORMAT))
                points_list.append(p)

            else:
                trajectory= Trajectory( points_list, tag_id=tag1)
                self.list_trajectories.append(trajectory)
                tag1=l[0]
                points_list = list()
                p = Point(l[1], l[2], datetime.strptime(l[3], TIMESTAMP_FORMAT))
                points_list.append(p)

        trajectory = Trajectory( points_list, tag_id=tag1)
        self.list_trajectories.append(trajectory)

    def read_single_traj_from_single_csv(self, path):
        tag_id = None
        col_list = [X_COLUMN, Y_COLUMN, TIME_COLUMN]
        df = pd.read_csv(path)  # , usecols=col_list)
        if TAG_COLUMN in df.columns:
            tag_id = df[TAG_COLUMN].iloc[0]

        df = pd.read_csv(path, usecols=col_list)[col_list]
        df.sort_values(by=[TIME_COLUMN])
        data_list = df.values.tolist()
        points_list = list()
        # self.list_trajectories=list()

        for l in data_list:
            p=Point(l[0], l[1], datetime.strptime(l[2],TIMESTAMP_FORMAT))
            points_list.append(p)

        trajectory = Trajectory( points_list, tag_id=tag_id)
        return trajectory


    def process_single_file_from_folder(self, f):
        f_output = os.path.basename(f)
        self.run_statistics_single_mode(f, self.output_folder + 'output_' + f_output)
        del f_output

    def process_one_trajectory_of_multi(self, traj):
        stats = StatisticsTrajectories(traj, self.output_file, multi_mode=2)
        stats.run()
        del stats

    def run_statistics_single_mode(self,  input_path_f, output_path):
        trajectory= self.read_single_traj_from_single_csv(input_path_f)
        stats = StatisticsTrajectories(trajectory, output_path,  multi_mode=0)
        results=stats.run()
        results.stamp()
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
            self.read_multi_traj_from_csv(input_file)
            trajectory1=self.list_trajectories[0]
            stats = StatisticsTrajectories(trajectory1, output_file,  multi_mode=1)
            stats.run()

            if self.parallelism:
                with ProcessPoolExecutor(max_workers=self.max_processors) as ex:
                    res = ex.map(self.process_one_trajectory_of_multi, self.list_trajectories[1:])
                return list(res)
            else:
                for traj in self.list_trajectories[1:]:
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

    stats=RunStatistics()

    ##statistics in single mode
    #input_file="./input/atc_7traj/10340900.csv"
    #output_file = "./output/stats_10340900.csv"
    #stats.run_statistics_single_mode(input_file, output_file)

    ##statistics in bulk mode, single file as input
    #input_path_f = "./input/atc_7traj.csv"
    #output_path_f = "./output/atc_stats_7traj.csv"
    #stats.run_statistics_multi_mode(input_file=input_path_f, output_file=output_path_f, max_processors=3)

    ##statistics in bulk mode, folder as input
    #input_path_folder = "./input/atc_7traj/"
    #output_path_folder = "./output/atc_stats/"
    #stats.run_statistics_multi_mode(input_folder=input_path_folder, output_folder=output_path_folder, max_processors=3)




