import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
import csv
import json
import os
import glob
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from datetime import datetime


from seqscan.data.stop import Stop
from seqscan.data.symbolic_trajectory import Symbolic_Trajectory
from tools.plot_symbolic_trajectories import PlotSymbolicTrajectories


with open('.\config.json') as f:
    config = json.load(f)

TAG_COLUMN=config["CSV_columns"]["TAG_COLUMN"]
IS_CARTESIAN=config["is_cartesian"]
TIMESTAMP_FORMAT = config["TIMESTAMP_FORMAT"]

STOP_ID_COLUMN=config["OUTPUT_STOPS_COLUMNS"]["STOP_LABEL"]
START_TIME_COLUMN=config["OUTPUT_STOPS_COLUMNS"]["START"]
END_TIME_COLUMN=config["OUTPUT_STOPS_COLUMNS"]["END"]
if IS_CARTESIAN:
    CENTROID_X_COLUMN=config["OUTPUT_STOPS_COLUMNS"]["CARTESIAN_CENTROID_X"]
    CENTROID_Y_COLUMN=config["OUTPUT_STOPS_COLUMNS"]["CARTESIAN_CENTROID_Y"]
else:
    CENTROID_X_COLUMN=config["OUTPUT_STOPS_COLUMNS"]["CENTROID_LAT"]
    CENTROID_Y_COLUMN=config["OUTPUT_STOPS_COLUMNS"]["CENTROID_LON"]

class RunSymbolicPlotter():


    def read_multi_traj_from_csv(self, path):
        col_list = [TAG_COLUMN, STOP_ID_COLUMN,START_TIME_COLUMN, END_TIME_COLUMN, CENTROID_X_COLUMN, CENTROID_Y_COLUMN]
        df = pd.read_csv(path, usecols=col_list)[col_list]
        data_list = df.values.tolist()
        stops_list = list()
        self.list_symbolic_trajectories = list()

        tag1 = data_list[0][0]
        for l in data_list:
            if l[0] == tag1:
                s = Stop(l[1], datetime.strptime(l[2], TIMESTAMP_FORMAT), datetime.strptime(l[3], TIMESTAMP_FORMAT),
                         l[4], l[5])
                stops_list.append(s)

            else:
                symbolic_trajectory = Symbolic_Trajectory(stops_list, tag_id=tag1)
                self.list_symbolic_trajectories.append(symbolic_trajectory)
                tag1 = l[0]
                stops_list = list()
                s = Stop(l[1], datetime.strptime(l[2], TIMESTAMP_FORMAT), datetime.strptime(l[3], TIMESTAMP_FORMAT),
                         l[4], l[5])
                stops_list.append(s)

        symbolic_trajectory = Symbolic_Trajectory(stops_list, tag_id=tag1)
        self.list_symbolic_trajectories.append(symbolic_trajectory)

    def read_single_traj_from_single_csv(self, path):
        col_list = [STOP_ID_COLUMN,START_TIME_COLUMN, END_TIME_COLUMN, CENTROID_X_COLUMN, CENTROID_Y_COLUMN]
        df = pd.read_csv(path, usecols=col_list)[col_list]
        data_list = df.values.tolist()
        stops_list = list()

        for l in data_list:
            s = Stop(l[0], datetime.strptime(l[1], TIMESTAMP_FORMAT), datetime.strptime(l[2], TIMESTAMP_FORMAT),
                     l[3], l[4])
            stops_list.append(s)

        symbolic_trajectory = Symbolic_Trajectory(stops_list)
        return symbolic_trajectory

    def process_single_file_from_folder(self, f):
        print('processing ', f)

        f_output = str(os.path.splitext(os.path.basename(f))[0]) + '.png'
        self.plot_symbolic_single_mode(f, self.output_folder + 'output_' + f_output)
        del f_output

    def process_one_trajectory_of_multi(self, symbolic_traj):
        output_file = self.output_folder + '/' + str(symbolic_traj.tag_id) + '.png'
        plot = PlotSymbolicTrajectories(symbolic_traj, output_file, multi_mode=2)
        plot.plot()
        del plot

    def plot_symbolic_single_mode(self, input_path_f, output_path):
        symbolic_trajectory = self.read_single_traj_from_single_csv(input_path_f)
        plot = PlotSymbolicTrajectories(symbolic_trajectory, output_path, multi_mode=0)
        plot.plot()

    def plot_symbolic_multi_mode(self, input_folder=None, output_folder=None, input_file=None, output_file=None,
                        max_processors=1):

        if input_file is None and input_folder is None:
            print('Please specify if input_file or input_folder')
            return
        elif input_file is not None and input_folder is not None:
            print('Please specify if input_file or input_folder, specifying both will create confusion')
            return
        elif output_file is not None:
            print('In case of trajectory plotter, only folders are accepted as output')
            return
        elif input_file is not None and output_folder is None:
            print('Please specify the output_folder')
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
            self.output_folder = output_folder
            self.read_multi_traj_from_csv(input_file)
            symbolic_trajectory1 = self.list_symbolic_trajectories[0]
            output_file1 = output_folder + '/' + str(symbolic_trajectory1.tag_id) + '.png'
            plot = PlotSymbolicTrajectories(symbolic_trajectory1, output_file1, multi_mode=1)
            plot.plot()

            if self.parallelism:
                with ProcessPoolExecutor(max_workers=self.max_processors) as ex:
                    res = ex.map(self.process_one_trajectory_of_multi, self.list_symbolic_trajectories[1:])
                return list(res)
            else:
                for traj in self.list_symbolic_trajectories[1:]:
                    self.process_one_trajectory_of_multi(traj)


        elif input_folder is not None:
            self.output_folder = output_folder
            csv_input_files = glob.glob(os.path.join(input_folder, "*.csv"))

            if self.parallelism:
                with ProcessPoolExecutor(max_workers=self.max_processors) as ex:
                    res = ex.map(self.process_single_file_from_folder, csv_input_files)
                return list(res)
            else:
                for f in csv_input_files:
                    self.process_single_file_from_folder(f)


if __name__ == '__main__':
        stops_plots = RunSymbolicPlotter()

        ## The input is a single file of 1 trajectory
        #input_path_file = "./output/seqscan_output/symbolic/output_symbolic10340900.csv"
        ##The output is a single PNG of the trajectory
        #output_path_file = "./output/plot_stops_10340900.png"
        ## Plot the trajectory using single mode
        #stops_plots.plot_symbolic_single_mode(input_path_file, output_path_file)

        ## The input is a single file of 1 trajectory, not cartesian, GeoLife example
        #input_path_file = "./output/symbolic_seqscan_geolife_example.csv"
        ##The output is a single PNG of the trajectory
        #output_path_file = "./output/plot_stops_geolife.png"
        ## Plot the trajectory using single mode
        #stops_plots.plot_symbolic_single_mode(input_path_file, output_path_file)

        ## The input is a single file of many trajectories
        #input_path_file = "./output/symbolic_seqscan_atc_7traj.csv"
        ## The output is a folder of multiple PNGs
        #output_folder = "./output/plots_stops_folder/"
        #stops_plots.plot_symbolic_multi_mode(input_file=input_path_file, output_folder=output_folder,max_processors=3)

        ##The input is a directory of many files
        #input_folder = "./output/seqscan_output/symbolic"
        # The output is a folder of multiple PNGs
        #output_folder = "./output/plots_stops_folder/"
        #stops_plots.plot_symbolic_multi_mode(input_folder=input_folder, output_folder=output_folder, max_processors=3)
