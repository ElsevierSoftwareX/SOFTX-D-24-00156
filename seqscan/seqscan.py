"""Implementation of the SEQSCAN algorithm on a single Object."""

# Standard modules
import numpy
import sys
import math
import time

from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict

# my modules
from .region import Region
from .point  import Point
from .feature import Feature
from .feature_point import FeaturePoint
from .rectangle import Rectangle

from .data.trajectory import Trajectory
from .data.point import Point as TrajectoryPoint

"""Implementation of the SEQSCAN algorithm on a single Object."""

# Standard modules
import numpy
import sys
import math
import time

from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
import csv
# my modules
from .region import Region
from .point import Point
from .feature import Feature
from .feature_point import FeaturePoint
from .rectangle import Rectangle

from .data import Trajectory
from .data import Point as TrajectoryPoint
import json

with open('./config.json') as f:
    config = json.load(f)
TAG_COLUMN = config["CSV_columns"]["TAG_COLUMN"]
CARTESIAN= config["is_cartesian"]

# Constants and helpers
EXCURSION='Excursion'
CLUSTERED='Residence'
TRANSITION='Migration'
NOISE='Noise'

MOVE_LABEL = "MOVE"
STOP_LABEL = "STOP"
    
class SeqScan():
    """Implementation of the SEQSCAN algorithm."""
    
    def __init__(self, trajectory:Trajectory, output_path, output_path_symbolic, silent=True, multi_mode=0):
        self.trajectory = trajectory
        self.silent = silent
        self.output_path=output_path
        self.output_path_symbolic=output_path_symbolic
        self.multi_mode=multi_mode

        self.is_cartesian = trajectory.is_cartesian
        if self.is_cartesian:
            self.distance = self._euclidian_distance
        else:
            self.distance = self._haversine_distance

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
    
    def add_cluster(self, cluster):
        """If cluster is not None, its final self is added to the correct set.
        Args:
            cluster (Region): the cluster
        """
        if cluster is not None:
            self.clusters.add(cluster.walk()) # final form
      
    def expand(self, active_cluster, point, neighborhood, n, start, end):
        """True if the given point is inside the active_cluster.
        
        Args:
            active_cluster (Region): the cluster we are trying to expand
            point (Point): the Point we are trying to add to the active_cluster
            neighborhood (list of Point): list of the point's neighbors
            n (int): min number of neighbors of a core point
            start (datetime): begin timestamp of the specified time frame
            end (datetime): end timestamp of the specified time frame

        """
        Region.phase = Region.EXPANSION
        Region.expansion_noise.add(point)
        point.update_neighbors(neighborhood, n, start, end)

        if active_cluster.start_context != start:
            raise ValueError("Extent not contextual region")

        belongs = point.is_inside(active_cluster)

        return belongs
        
    # As in pseudo-code, so it won't be inlined.
    def find_cluster(self, point, neighborhood, n, start, end, active_cluster):
        """Returns the first persistent Region this Point belongs to.
        Args:
            point (Point): a point
            neighborhood (list of Point): list of the point's neighbors
            n (int): min number of neighbors of a core point
            start (datetime): begin timestamp of the specified time frame
            end (datetime): end timestamp of the specified time frame
            active_cluster (Region): the active cluster
        """
        Region.phase = Region.LOOK_UP
        Region.look_up_noise.add(point)
        point.update_neighbors(neighborhood, n, start, end)


        for r in point.get_regions(start, end):
            if r.is_persistent():
                # new cluster found
                return r
                
        # no cluster found
        return None

    
    def run(self, distance, n_points, presence):
        """Excecutes the SEQSCAN clustering algorithm on a single object.
        """
        self.dataset = self.load_datapoints(self.trajectory, self.is_cartesian)
        progressInd = 0
        self.featuresCount = len(self.dataset)
        try:
 
            self.clusters = set()

            # Region init
            Region.threshold = timedelta(seconds=presence)

            # init
            time_start = datetime.min
            time_end   = datetime.min

            active_cluster = None

            # Region init
            Region.counter = 0
            Region.expansion_log   = set()
            Region.expansion_noise = set()
            Region.look_up_log   = set()
            Region.look_up_noise = set()
            Region.phase = Region.EXPANSION
            Region.log = []

            for point in self.dataset:

                square = Rectangle(point.geometry, point.geometry)
                square = square.buffer(distance + 1)

                inner_square = Rectangle(point.geometry, point.geometry)
                inner_square = inner_square.buffer(distance * 0.7)

                if active_cluster is None:
                    regions = Region.look_up_log
                    noise   = Region.look_up_noise
                else:
                    regions = Region.expansion_log
                    noise   = Region.expansion_noise

                candidate_points = set(q for q
                    in noise
                    if square.contains_point(q.geometry)
                )

                for r in regions:
                    if r.in_time_frame(time_start, time_end):
                        r.query(square, candidate_points)


                neighborhood = [q for q
                    in candidate_points
                    if (inner_square.contains_point(q.geometry) or 
                        self.distance(point.geometry.array_rep[0], point.geometry.array_rep[1], q.geometry.array_rep[0], q.geometry.array_rep[1]) <= distance
                    )
                ]
                neighborhood.insert(len(neighborhood), point)
                
                if active_cluster is not None and self.expand(
                    active_cluster,
                    point,
                    neighborhood,
                    n_points,
                    time_start,
                    point.time
                ):
                    time_end = point.time

                    Region.look_up_log = set()
                    Region.look_up_noise = set()

                    active_cluster =active_cluster.walk()

                else:
                    # filters the neighbors
                    neigh = [n for n
                        in neighborhood
                        if time_end < n.time <= point.time
                    ]

                    next_cluster = self.find_cluster(
                        point,
                        neigh,
                        n_points,
                        time_end,
                        point.time,
                        active_cluster
                    )
                    if next_cluster is not None:
                        if active_cluster is not None:
                            self.add_cluster(active_cluster)
                        time_start = time_end
                        time_end = point.time
                        active_cluster = next_cluster.walk()

                        Region.expansion_log = Region.look_up_log
                        Region.look_up_log = set()

                        Region.expansion_noise = Region.look_up_noise
                        Region.look_up_noise = set()
                
                progressInd +=1
                self.update_progress((progressInd/self.featuresCount)*100)

            # unfinished business
            self.add_cluster(active_cluster)
            self._analyze(self.dataset)

            return self.exportOutputFiles()

        except MemoryError as error:
            print("Out of memory while processing\n{}\n".format(error))
            self.clearObjectMemory(self.dataset)

    def clearObjectMemory(self, dataset):
        try:
            if dataset is not None:
                for p in dataset:
                    del p.regions

            del Region.expansion_log
            del Region.expansion_noise
            del Region.look_up_log
            del Region.look_up_noise
            del Region.log
            #del dataset[:]
            #del dataset
            #del self

        except Exception as exception:
            print(exception)

    def _analyze(self, dataset):
        """Cluster labelling and noise classification."""
        
        # clustered points labelling
        for cluster in self.clusters:
            for point in cluster.points:
                point.cluster = cluster

        # previous cluster
        prev = None
        # noise labelling
        for point in dataset:
            if point.cluster is None:
                point.prev = prev
            else:
                prev = point.cluster
        # next cluster
        next = None
        for point in reversed(dataset):
            if point.cluster is None:
                point.next = next
                    
                # increase cluster excursion counter
                if point.next is point.prev and next is not None:
                    next.noise += 1
            else:
                next = point.cluster

        # clustered points ranked
        for cluster in self.clusters:
            densities_set=set()
            for point in cluster.points:
                point.set_len_neighbors()
                densities_set.add(point.get_len_neighbors())

            densities_list=list(densities_set)
            densities_list.sort(reverse=True)
            densities_rank_dict={}
            for i in range(len(densities_list)):
                r=i+1
                densities_rank_dict[densities_list[i]]=r
            for point in cluster.points:
                point.set_density_rank(densities_rank_dict[point.get_len_neighbors()])

    def exportOutputFiles(self):
        annotated_trajectory = Trajectory()

        cluster_counter = 0
        current_cluster = -1
        for point in self.dataset:
            p = TrajectoryPoint(point.geometry.lat, point.geometry.lon, point.time)
            #if self.multi_mode==1 or self.multi_mode==2:
            if self.trajectory.tag_id is not None:
                p.annotations[TAG_COLUMN] = self.trajectory.tag_id

            if (point.cluster is None) and (point.next is not None) and (point.prev is not None):
                if point.prev.id == point.next.id:
                    p.annotations["cluster"] = -1
                    p.annotations["class"] = MOVE_LABEL  # "EXCURSION"
                    p.annotations["type"] = "excursion"
                    p.annotations["details"] = "of cluster " + str(cluster_counter)

                else:
                    p.annotations["cluster"] = -1
                    p.annotations["class"] = MOVE_LABEL
                    p.annotations["type"] = "transition"
                    p.annotations["details"] = "from cluster " + str(cluster_counter)

            else:
                if point.cluster is not None:
                    if point.cluster.id != current_cluster:
                        cluster_counter = cluster_counter + 1
                        current_cluster = point.cluster.id

                    p.annotations["cluster"] = str(cluster_counter)
                    p.annotations["class"] = "{}_{}".format(STOP_LABEL, cluster_counter)
                    p.annotations["type"] = "cluster"
                    p.annotations["details"] = "cluster # " + str(cluster_counter)

                else:
                    p.annotations["cluster"] = -1
                    p.annotations["class"] = MOVE_LABEL
                    p.annotations["type"] = "noise"
                    p.annotations["details"] = "before/after clustering"

            annotated_trajectory.add_point(p)

        self.clearObjectMemory(self.dataset)

        annotated_trajectory.export_to_csv(self.output_path, writing_mode=self.multi_mode)
        self.exportSymbolicTrajectory(self.output_path_symbolic, writing_mode=self.multi_mode)
        return annotated_trajectory


    def exportSymbolicTrajectory(self, path, writing_mode=0):

        if writing_mode==0 or writing_mode==1:
            with open(path, "w", newline='') as f:
                writer = csv.writer(f)
                if CARTESIAN:
                    writer.writerow([TAG_COLUMN,"stop_id", "start_time", "end_time", "centroid_x", "centroid_y"])  # Write header
                else:
                    writer.writerow([TAG_COLUMN, "stop_id", "start_time", "end_time", "centroid_lat", "centroid_lon"])  # Write header
                i=1
                for cluster in self.clusters:
                    c=cluster.compute_centroid()
                    writer.writerow([self.trajectory.tag_id, "STOP_"+str(i),
                                     cluster.first_timestamp(), cluster.last_timestamp(),
                                     c[0], c[1]])
                    i+=1

        elif writing_mode==2:
            with open(path, "a", newline='') as f:
                writer = csv.writer(f)
                i = 1
                for cluster in self.clusters:
                    c = cluster.compute_centroid()
                    writer.writerow(
                        [self.trajectory.tag_id, "STOP_" + str(i),
                         cluster.first_timestamp(), cluster.last_timestamp(),
                         c[0], c[1]])
                    i += 1


    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        dlon = math.radians(lon2) - math.radians(lon1) 
        dlat = math.radians(lat2) - math.radians(lat1) 
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
       
        return 2 * math.asin(math.sqrt(a))  * 6371009
   
    def _euclidian_distance(self, lat1, lon1, lat2, lon2):
        return math.sqrt((lon1-lon2)**2 + (lat1-lat2)**2)

    def update_progress(self, completion):
        pass

