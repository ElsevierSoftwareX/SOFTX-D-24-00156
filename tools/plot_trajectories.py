
# Standard modules
import os
import numpy
import statistics
import sys
import math
import time


from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict

from seqscan.point import Point
from seqscan.feature import Feature
from seqscan.feature_point import FeaturePoint

from seqscan.data.trajectory import Trajectory
from seqscan.data.point import Point as TrajectoryPoint

import pandas as pd
import matplotlib.pyplot as plt
import os



class PlotTrajectories():

    
    def __init__(self, trajectory:Trajectory, output_path, multi_mode=0):
        self.trajectory = trajectory
        self.output_path=output_path
        self.multi_mode = multi_mode
        self.is_cartesian = trajectory.is_cartesian

    def load_datapoints(self, trajectory, cartesian):
        dataset = []
        for p in trajectory:
            point = Point(
                FeaturePoint(p.lat, p.lon, cartesian),
                p.timestamp
            )
            dataset.append(point)

        dataset.sort(key = lambda p : p.time)
        return dataset



    def plot(self):
        fig = plt.figure(figsize=(15, 12))

        self.dataset = self.load_datapoints(self.trajectory, self.is_cartesian)
        list_x=[p.geometry.array_rep[0] for p in self.dataset]
        list_y=[p.geometry.array_rep[1] for p in self.dataset]
        list_t=[p.time.timestamp() for p in self.dataset]

        cmap = plt.get_cmap('cool')

        ax = fig.add_subplot(111, projection='3d')
        for i in range(len(list_x) - 1):
            plt.plot(list_x[i:i+2], list_y[i:i+2],list_t[i:i+2], color=cmap(i / len(list_x)), linewidth=5)

        #ax.plot(list_x, list_y, list_t, linewidth=5)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Time Stamp')


        plt.savefig(self.output_path)
        plt.close(fig)





