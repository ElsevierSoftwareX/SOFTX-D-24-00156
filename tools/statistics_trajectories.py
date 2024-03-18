
# Standard modules
import os
import numpy
import statistics
import sys
import math
import time


from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict

# my modules
print (os.getcwd())
from seqscan.point import Point
from seqscan.feature import Feature
from seqscan.feature_point import FeaturePoint

from seqscan.data.trajectory import Trajectory
from seqscan.data.point import Point as TrajectoryPoint
import csv
import json

with open('.\config.json') as f:
    config = json.load(f)
TAG_COLUMN=config["CSV_columns"]["TAG_COLUMN"]
TIME_UNIT = config["UNITS"]["TIME"]

class StatisticsTrajectories():

    
    def __init__(self, trajectory:Trajectory, output_path,  multi_mode=0):
        self.trajectory = trajectory
        self.output_path=output_path
        self.multi_mode=multi_mode

        self.is_cartesian = trajectory.is_cartesian
        if self.is_cartesian:
            self.distance = self._euclidian_distance
        else:
            self.distance = self._haversine_distance

        self.stats_results= StatResult()

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

    
    def distances_two_points(self, p, q):
        self.distance(p.geometry.array_rep[0], p.geometry.array_rep[1], q.geometry.array_rep[0],
                      q.geometry.array_rep[1])

    def run(self):
        """Excecutes the statistics on a single object.
        """
        self.dataset = self.load_datapoints(self.trajectory, self.is_cartesian)

        step_lengths=[]
        step_durations=[]

        for i in range(0, len(self.dataset)-1):
            j=i+1
            p=self.dataset[i]
            q=self.dataset[j]
            step_lengths.append(self.distance(p.geometry.array_rep[0], p.geometry.array_rep[1],
                                              q.geometry.array_rep[0], q.geometry.array_rep[1]))

            step_durations.append((q.time- p.time).total_seconds())


        self.stats_results.dict_step_length['mean']= statistics.mean(step_lengths)
        self.stats_results.dict_step_length['median']= statistics.median(step_lengths)
        self.stats_results.dict_step_length['std']=statistics.pstdev(step_lengths) #population stdev, stdev instead is calculated over a sample only
        self.stats_results.dict_step_length['min']=min(step_lengths)
        self.stats_results.dict_step_length['max']= max(step_lengths)

        self.stats_results.dict_step_duration['mean'] = self.convert_duration_from_s(statistics.mean(step_durations))
        self.stats_results.dict_step_duration['median'] = self.convert_duration_from_s(statistics.median(step_durations))
        self.stats_results.dict_step_duration['std'] = self.convert_duration_from_s(statistics.pstdev(step_durations))
        self.stats_results.dict_step_duration['min'] = self.convert_duration_from_s(min(step_durations))
        self.stats_results.dict_step_duration['max'] = self.convert_duration_from_s(max(step_durations))

        self.stats_results.trajectory_number_points= len(self.dataset)

        self.stats_results.trajectory_duration= self.dataset[-1].time-self.dataset[0].time

        self.exportStats_tocsv()
        return self.stats_results


    def convert_distance_unit_from_m(self, dist):
        #no need for this because the coordinates are already taken as they are
        #the coordinates are not converted to m to convert them back
        pass

    def convert_duration_from_s(self, t):
        if TIME_UNIT=='min':
            return float(t)/60.0
        elif TIME_UNIT=='d':
            return float(t)/(3600.0*24.0)
        return t


    def exportStats_tocsv(self):
        csv_columns = ["mean step length", "median step length", "std step length", "min step length",
                       "max step length",
                       "mean step duration", "median step duration", "std step duration", "min step duration",
                       "max step duration",
                       "number points", "total duration"]


        csv_data = {
            "mean step length": self.stats_results.dict_step_length['mean'],
            "median step length": self.stats_results.dict_step_length['median'],
            "std step length": self.stats_results.dict_step_length['std'],
            "min step length": self.stats_results.dict_step_length['min'],
            "max step length": self.stats_results.dict_step_length['max'],

            "mean step duration": self.stats_results.dict_step_duration['mean'],
            "median step duration": self.stats_results.dict_step_duration['median'],
            "std step duration": self.stats_results.dict_step_duration['std'],
            "min step duration": self.stats_results.dict_step_duration['min'],
            "max step duration": self.stats_results.dict_step_duration['max'],

            "number points": self.stats_results.trajectory_number_points,
            "total duration": self.stats_results.trajectory_duration,
        }

        #if self.multi_mode==1 or self.multi_mode==2:
        if self.trajectory.tag_id is not None:
                csv_columns.insert(0,TAG_COLUMN)
                csv_data[TAG_COLUMN]=self.trajectory.tag_id


        if self.multi_mode==0 or self.multi_mode==1:
            with open(self.output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_columns)
                writer.writeheader()
                writer.writerow(csv_data)

        elif self.multi_mode==2:
            with open(self.output_path, mode='a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=csv_columns)
                writer.writerow(csv_data)

    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        dlon = math.radians(lon2) - math.radians(lon1) 
        dlat = math.radians(lat2) - math.radians(lat1) 
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
       
        return 2 * math.asin(math.sqrt(a))  * 6371009
   
    def _euclidian_distance(self, lat1, lon1, lat2, lon2):
        return math.sqrt((lon1-lon2)**2 + (lat1-lat2)**2)

    def update_progress(self, completion):
        pass

class StatResult():

    def __init__(self):
        self.dict_step_length = {}
        self.dict_step_duration = {}
        self.trajectory_duration=0
        self.trajectory_number_points=0

    def stamp(self):
        print (self.dict_step_length)
        print (self.dict_step_duration)
        print(self.trajectory_number_points)
        print(self.trajectory_duration)
