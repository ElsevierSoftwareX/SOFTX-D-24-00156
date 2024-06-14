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
from seqscan.data.stop_point import Stop_Point
import csv
import json
import pandas as pd

from itertools import groupby
from operator import attrgetter


with open('.\config.json') as f:
    config = json.load(f)
TAG_COLUMN=config["CSV_columns"]["TAG_COLUMN"]
TIME_COLUMN=config["CSV_columns"]["TIME_COLUMN"]
TIMESTAMP_FORMAT = config["TIMESTAMP_FORMAT"]
TIME_UNIT=config["UNITS"]["TIME"]
CLASS_COLUMN=config["OUTPUT_COLUMNS"]["CLASS"]
TYPE_COLUMN=config["OUTPUT_COLUMNS"]["TYPE"]
DETAILS_COLUMN=config["OUTPUT_COLUMNS"]["DETAILS"]

class StatisticsStops():

    
    def __init__(self, list_stop_points, output_path, tag_id=None, multi_mode=0):
        self.list_stop_points = list_stop_points
        self.output_path=output_path
        self.multi_mode=multi_mode
        self.tag_id=tag_id

        self.stats_results= StatResult()

        output_directory = os.path.dirname(self.output_path)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)



    def run(self):

        stop_durations=[]
        stop_presences=[]
        stop_p_d=[]

        distinct_cl = set(point.cl for point in self.list_stop_points)
        distinct_cl.discard(-1)

        self.stats_results.number_stops=len(distinct_cl)

        if self.stats_results.number_stops>0:
            cl_segments = defaultdict(list)
            for cl in distinct_cl:
                cl_points = [point for point in self.list_stop_points if point.cl == cl]
                if cl_points:
                    min_timestamp = min(datetime.strptime(point.timestamp, TIMESTAMP_FORMAT) for point in cl_points)
                    max_timestamp = max(datetime.strptime(point.timestamp, TIMESTAMP_FORMAT) for point in cl_points)
                    cl_segments[cl] = (min_timestamp, max_timestamp)

            for cl, (min_ts, max_ts) in cl_segments.items():
                print(f"Segment for cl '{cl}':")
                print(f"  Min Timestamp: {min_ts}")
                print(f"  Max Timestamp: {max_ts}")
                print()
                stop_durations.append((max_ts-min_ts).total_seconds())

                filtered_stop_points = [point for point in self.list_stop_points
                                        if min_ts <= datetime.strptime(point.timestamp, TIMESTAMP_FORMAT) <= max_ts]

                current_cl_presence=0
                for i in range(0, len(filtered_stop_points) - 1):
                    j = i + 1
                    p = filtered_stop_points[i]
                    q = filtered_stop_points[j]
                    if p.cl == q.cl and p.cl > 0:  # p and q in the same stop and are not excursion
                        dtp = datetime.strptime(p.timestamp, TIMESTAMP_FORMAT)
                        dtq = datetime.strptime(q.timestamp, TIMESTAMP_FORMAT)
                        difference_step_time = (dtq - dtp).total_seconds()
                        current_cl_presence += difference_step_time
                stop_presences.append(current_cl_presence)
                stop_p_d.append(current_cl_presence/(max_ts-min_ts).total_seconds())


            self.stats_results.dict_stop_duration['mean'] = statistics.mean(stop_durations)
            self.stats_results.dict_stop_duration['median'] = statistics.median(stop_durations)
            self.stats_results.dict_stop_duration['std'] = statistics.pstdev(stop_durations)
            self.stats_results.dict_stop_duration['min'] = min(stop_durations)
            self.stats_results.dict_stop_duration['max'] = max(stop_durations)

            self.stats_results.avg_p_d= statistics.mean(stop_p_d)
        else:
            self.stats_results.dict_stop_duration['mean'] = 0
            self.stats_results.dict_stop_duration['median'] = 0
            self.stats_results.dict_stop_duration['std'] = 0
            self.stats_results.dict_stop_duration['min'] = 0
            self.stats_results.dict_stop_duration['max'] = 0

            self.stats_results.avg_p_d = 0

        self.exportStats_tocsv()
        return self.stats_results



    def exportStats_tocsv(self):
        csv_columns = ["mean stop duration", "median stop duration", "std stop duration", "min stop duration",
                       "max stop duration",
                       "number stops", "avg P/D"]


        csv_data = {
            "number stops": self.stats_results.number_stops,
            "avg P/D": self.stats_results.avg_p_d,

            "mean stop duration": self.convert_duration_from_s(self.stats_results.dict_stop_duration['mean']),
            "median stop duration": self.convert_duration_from_s(self.stats_results.dict_stop_duration['median']),
            "std stop duration": self.convert_duration_from_s(self.stats_results.dict_stop_duration['std']),
            "min stop duration": self.convert_duration_from_s(self.stats_results.dict_stop_duration['min']),
            "max stop duration": self.convert_duration_from_s(self.stats_results.dict_stop_duration['max'])
        }

        #if self.multi_mode==1 or self.multi_mode==2:
        if self.tag_id is not None:
                csv_columns.insert(0,TAG_COLUMN)
                csv_data[TAG_COLUMN]=self.tag_id


        if self.multi_mode==0 or self.multi_mode==1:
            with open(self.output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_columns)
                writer.writeheader()
                writer.writerow(csv_data)

        elif self.multi_mode==2:
            with open(self.output_path, mode='a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=csv_columns)
                writer.writerow(csv_data)

    def convert_duration_from_s(self, t):
        if TIME_UNIT=='min':
            return float(t)/60.0
        elif TIME_UNIT=='d':
            return float(t)/(3600.0*24.0)
        return t



class StatResult():

    def __init__(self):
        self.dict_stop_duration = {}
        self.number_stops=0
        self.avg_p_d=0

    def stamp(self):
        print (self.dict_stop_duration)
        print (self.number_stops)
        print(self.avg_p_d)
