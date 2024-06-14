from __future__ import annotations
from collections.abc import Sequence

from csv import DictReader, DictWriter
from datetime import datetime


from .stop import Stop
import json

with open('./config.json') as f:
    config = json.load(f)
STOP_ID_COLUMN = config["OUTPUT_STOPS_COLUMNS"]["STOP_LABEL"]
START_TIME_COLUMN = config["OUTPUT_STOPS_COLUMNS"]["START"]
END_TIME_COLUMN = config["OUTPUT_STOPS_COLUMNS"]["END"]
IS_CARTESIAN=config["is_cartesian"]
if IS_CARTESIAN:
        CENTROID_X_COLUMN = config["OUTPUT_STOPS_COLUMNS"]["CARTESIAN_CENTROID_X"]
        CENTROID_Y_COLUMN = config["OUTPUT_STOPS_COLUMNS"]["CARTESIAN_CENTROID_Y"]
else:
        CENTROID_X_COLUMN = config["OUTPUT_STOPS_COLUMNS"]["CENTROID_LAT"]
        CENTROID_Y_COLUMN = config["OUTPUT_STOPS_COLUMNS"]["CENTROID_LON"]

TIMESTAMP =config["CSV_columns"]["TIME_COLUMN"]
TIMESTAMP_FORMAT =config["TIMESTAMP_FORMAT"]
TAG_COLUMN = config["CSV_columns"]["TAG_COLUMN"]
CARTESIAN= config["is_cartesian"]


class Symbolic_Trajectory():

    def __init__(self, stops:list(Stop)=None, sort=True, tag_id=None):
        super().__init__()

        self.tag_id=tag_id
        self.is_cartesian=IS_CARTESIAN

        if stops is None:
            self._data = []
        else:
            self._data = stops

        if stops and sort:
            self._data.sort(key= lambda p : p.start_time)

    @property
    def length(self):
        return len(self._data)
    
    def get_stop(self, index):
        if len(self._data) < index:
            raise IndexError()
        
        return self._data[index] 


    def add_stop(self, stop:Stop):
        self._data.append(stop.copy())



