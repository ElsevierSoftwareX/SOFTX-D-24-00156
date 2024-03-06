import pandas as pd
import os
import glob
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

from tools.plot_trajectories import PlotTrajectories


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



class RunPlotter():


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
        col_list = [ X_COLUMN, Y_COLUMN, TIME_COLUMN ]
        df = pd.read_csv(path, usecols=col_list)[col_list]
        data_list= df.values.tolist()
        points_list=list()

        for l in data_list:
            p=Point(l[0], l[1], datetime.strptime(l[2],TIMESTAMP_FORMAT))
            points_list.append(p)

        trajectory = Trajectory( points_list)
        return trajectory


    def process_single_file_from_folder(self, f):
        #print('processing ', f)

        f_output = str(os.path.splitext(os.path.basename(f))[0])+'.png'
        self.plot_single_mode(f, self.output_folder + 'output_' + f_output)
        del f_output


    def process_one_trajectory_of_multi(self, traj):
        output_file=self.output_folder+'/' + str(traj.tag_id) + '.png'
        plot = PlotTrajectories(traj, output_file, multi_mode=2)
        plot.plot()
        del plot

    def plot_single_mode(self,  input_path_f, output_path):
        trajectory= self.read_single_traj_from_single_csv(input_path_f)
        plot = PlotTrajectories(trajectory, output_path,  multi_mode=0)
        plot.plot()

    def plot_multi_mode(self, input_folder=None, output_folder=None, input_file=None, output_file=None, max_processors=1):

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

        self.max_processors=max_processors

        if max_processors>1:
            self.parallelism=True
        else:
            self.parallelism=False

        if input_file is not None:
            self.output_folder=output_folder
            self.read_multi_traj_from_csv(input_file)
            trajectory1=self.list_trajectories[0]
            output_file1=output_folder+'/'+str(trajectory1.tag_id)+'.png'
            plot = PlotTrajectories(trajectory1, output_file1,  multi_mode=1)
            plot.plot()

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

    m= RunPlotter()

    #plotter = RunPlotter()

    # The input is a single file of 1 trajectory
    #input_path_file = "./input/atc_7traj/10340900.csv"
    # The output is a single PNG of the trajectory
    #output_path_file = "./output/plot_10340900.png"

    # Plot the trajectory using single mode
    #plotter.plot_single_mode(input_path_file,
    #                         output_path_file)



