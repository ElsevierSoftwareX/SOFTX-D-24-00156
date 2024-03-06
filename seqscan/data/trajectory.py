from __future__ import annotations
from collections.abc import Sequence

from csv import DictReader, DictWriter
from datetime import datetime
from math import sin, cos, asin, radians, sqrt

from .point import Point
import json

with open('./config.json') as f:
    config = json.load(f)



class Trajectory(Sequence):

    LATITUDE = config["CSV_columns"]["X_COLUMN"]
    LONGITUDE = config["CSV_columns"]["Y_COLUMN"]
    TIMESTAMP =config["CSV_columns"]["TIME_COLUMN"]
    TIMESTAMP_FORMAT =config["TIMESTAMP_FORMAT"]
    TAG_COLUMN = config["CSV_columns"]["TAG_COLUMN"]
    CARTESIAN= config["is_cartesian"]

    EARTH_RADIUS = 6371009

    #def __init__(self, cartesian=True , points:list(Point)=None, sort=True, tag_id=None):
    def __init__(self, points:list(Point)=None, sort=True, tag_id=None):
        super().__init__()

        self.tag_id=tag_id

        if points is None:
            self._data = []
        else:
            self._data = points

        self.is_cartesian = config["is_cartesian"]
        if self.is_cartesian:
            self.__dist_func = self._euclidian_distance
        else:
            self.__dist_func = self._haversine_distance

        if points and sort:
            self._data.sort(key= lambda p : p.timestamp)

    @property
    def length(self):
        return len(self._data)
    
    def get_point(self, index):
        if len(self._data) < index:
            raise IndexError()
        
        return self._data[index] 

    def get_points(self, start_index, end_index):
        if len(self._data) < end_index or start_index < 0:
            raise IndexError()
        
        return self._data[start_index:end_index]

    def add_point(self, point:Point):
        self._data.append(point.copy())

    def delta_time(self, idx1, idx2):
        return self._data[idx2].timestamp - self._data[idx1].timestamp

    def distance(self, idx1, idx2):
        return self.__dist_func(idx1, idx2)

    def group_by_annotation(self, annotation, exclude=None):
        groups = {}
        for p in self._data:
            cl = p.annotations[annotation]
            
            if cl in groups:
                groups[cl].append(p)
            else:
                groups[cl] = [p]

        if exclude is not None:
            for e in exclude:
                try:
                    del groups[e]
                except:
                    pass

        for k, v in groups.items():
            v.sort(key=lambda p : p.timestamp)

        return groups

    def get_annotations(self):
        return list(self._data[0].annotations.keys())
    
    def export_to_csv(self, path, lat=LATITUDE, lon=LONGITUDE, ts=TIMESTAMP, ts_format=TIMESTAMP_FORMAT, writing_mode=0):
        res = []
        for point in self._data:
            p = {
                lat: point.lat,
                lon: point.lon,
                ts: point.timestamp.strftime(ts_format)
            }
            for k, v in point.annotations.items():
                p[k] = v
            res.append(p)
        
        if writing_mode==0 or writing_mode==1:
            with open(path, "w") as f:
                #print(res[0].keys())
                w = DictWriter(f, fieldnames=res[0].keys(), lineterminator="\n")
                w.writeheader()
                w.writerows(res)

        elif writing_mode==2:
            with open(path, "a") as f:
                #print(res[0].keys())
                w = DictWriter(f, fieldnames=res[0].keys(), lineterminator="\n")
                w.writerows(res)

    def _haversine_distance(self, idx1, idx2):
        p1 = self.get_point(idx1)
        p2 = self.get_point(idx2)

        dlon = radians(p2.lon) - radians(p1.lon) 
        dlat = radians(p2.lat) - radians(p1.lat) 
        a = sin(dlat/2)**2 + cos(radians(p1.lat)) * cos(radians(p2.lat)) * sin(dlon/2)**2
    
        return 2 * asin(sqrt(a)) * self.EARTH_RADIUS

    def _euclidian_distance(self, idx1, idx2):
        p1 = self.get_point(idx1)
        p2 = self.get_point(idx2)

        return sqrt((p1.lon-p2.lon)**2 + (p1.lat-p2.lat)**2)

    def __getitem__(self, i):
        return self._data[i]
    
    def __len__(self):
        return len(self._data)
    
    @staticmethod
    def from_csv(path, cartesian:bool, lat=LATITUDE, lon=LONGITUDE, ts=TIMESTAMP, ts_format=TIMESTAMP_FORMAT, annotations:list(str)=None) -> Trajectory:
        with open(path) as f:
            data = list(DictReader(f))
        
        return Trajectory.from_dict_list(data, cartesian, lat, lon, ts, ts_format, annotations)

    @staticmethod
    def from_dict_list(data, cartesian:bool, lat=LATITUDE, lon=LONGITUDE, ts=TIMESTAMP, ts_format=TIMESTAMP_FORMAT, annotations:list(str)=None):
        l = []
        for row in data:
                latitude = float(row[lat])
                longitude = float(row[lon])
                if not cartesian:
                    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                        raise ValueError("Illegal value for latitude or longitude")
                
                ann = {}
                if annotations != None:  
                    for a in annotations:
                        ann[a] = row[a]   
   
                timestamp  = datetime.strptime(row[ts], ts_format)

                p = Point(latitude, longitude, timestamp, ann)
                l.append(p)

        return Trajectory(points=l, cartesian=cartesian)

