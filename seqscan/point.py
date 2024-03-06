"""Point implementation for the SEQSCAN algorithm."""

# Standard modules 
from datetime import datetime

# My modules
from .region import Region, LeafRegion, NodeRegion

class Point(object):
    """Point implementation for the SEQSCAN algorithm."""
    
    counter = None             # id generator
    
    def __init__(self, geometry, time):
        """Constructor.
        
        Args:
            geometry (FeaturePoint) : the geometry,lat,lon,x and y...
            time (datetime) : the observation timestamp

        Note:
            ids are generated using the class counter: this technique is NOT 
            thread-safe.
        """
        
        if (Point.counter is None):
            Point.counter = 0
		
        self.id = Point.counter
        self.geometry = geometry
        self.time = time


        self.core=False
        self.len_neigh=0
        self.density_rank=0

        # self.neighbors : set of neighbors of this point; includes self
        self.neighbors = set([self])
        # regions containing the point as a core, those regions are sorted by their time context, in the same context, the point could not be a core in two different regions
        self.regions = {}

        # for labelling convenience
        self.cluster = None
        
        # noise labelling
        self.prev = None
        self.next = None
        
        # region log
        self.first = None

        Point.counter += 1
        
    def __repr__(self):
        return '( id: %d, geometry: %s, time: %s)' % (
            self.id,
            self.geometry,
            self.time
        )
     
    def is_dense(self, threshold, start, end=None):
        """True if this Point is dense in the specified time frame.
        
        A Point is dense (w.r.t. a time frame) if it has at least threshold 
        neighbors (in the specified time frame).
        
        Args:
            threshold (int): min number of neighbors for a dense point
            start (datetime): begin timestamp of the time frame
            end (datetime): end timestamp of the time frame, defaults to None
            
        Note:
            this implementation checks only that the neighbors are found AFTER
            the beginning of the time frame, i.e. ignores the end parameter.
        """
        if len([p for p in self.neighbors if p.time > start]) >= threshold:
            self.core=True
            return True
        else:
            return False

    def is_core(self, start, end):
        """True if this Point is a core point in the specified time frame.
        
        A Point is a core point w.r.t. a time frame if any of the Regions it 
        belongs to is contained in the specified time frame.
        
        Args:
            start (datetime): begin timestamp of the time frame
            end (datetime): end timestamp of the time frame, defaults to None
            
        Note:
            this implementation checks only that the Regions are found AFTER
            the beginning of the time frame, i.e. ignores the end parameter.
        """


        if start in self.regions :
            self.core=True
            return True

        return False

    def is_border(self, start, end):
        """True if this Point is a border point in the specified time frame.
        
        A Point is a border point (w.r.t. a time frame) if any of its neighbors 
        is a core point in the same time frame.
        
        Args:
            start (datetime): begin timestamp of the time frame
            end (datetime): end timestamp of the time frame, defaults to None
            
        Note:
            this implementation checks only that the Regions are found AFTER
            the beginning of the time frame, i.e. ignores the end parameter.
        """
        return any(p.is_core(start, end) for p in self.neighbors)
        
    def neighboring_regions(self, start, end):
        """Returns the Regions this border Point is part of w.r.t. a time frame.
        
        Args:
            start (datetime): begin timestamp of the time frame
            end (datetime): end timestamp of the time frame, defaults to None
           
        Note:
            This implementation checks only that the Regions are found AFTER
            the beginning of the time frame, i.e. ignores the end parameter.
        """

        result = set()

        for n in self.neighbors:
            if n.is_core(start, end):
                result.add(n.get_core_region(start,end))
        return result



    def get_regions(self, start, end):
        """Returns the set of Regions this point belongs to in the specified 
        time frame.
        """
        result=set()

        if start in self.regions:
            result.add(self.get_core_region(start,end))

        elif self.is_border(start, end):
            result = self.neighboring_regions(start, end)

        # single return statement
        return result
        
    def is_inside(self, region):
        """True if this Point belongs to the specified Region."""
        return self in region.walk()

    def add_core_region (self,region,start,end):

        if start in self.regions:
            raise ValueError("look like a point is core in two regions with same context")
            return
        self.regions[start]=region

    def get_core_region(self, start,end):
        return self.regions[start].walk()

    def update_neighbors(self, neighbors, threshold, start, end):
        """Updates this Point's neighborhood.
        
        1. all the Points in neighbors are added to this Point neighbor-set
        2. this Point is added to the neighbor-set of each (new) neighbor p
        3.1 if p was a core point we add this Point to p's Regions as border, 
            then finish
        3.2 if p became a core point after the addition of this Point
        3.2.1. if it was a border point, all its Regions are merged into a new 
            one and all its neighbors (w.r.t. the specified time frame) are 
            added to this Region
        3.2.2. if it wasn't a core point, a new Region is created with p as core
            and all p's neighbors (w.r.t. the specified time frame) as border
           
        Args:
            neighbors: a list of points
            threshold (int): min number of neighbors of a core point
            start (datetime): begin timestamp of the time frame
            end (datetime): end timestamp of the time frame, defaults to None
            
        Note:
            This implementation checks only that the Points are found AFTER
            the beginning of the time frame, i.e. ignores the end parameter.
        """


        self.neighbors.update(neighbors)



        for p in neighbors: # scans only the **new** ones
            
            # Adds this point to its neighbors' neighborood
            #if p !=self
            p.neighbors.add(self)
            # if p already has a region, we add this point to p's regions 
            # as a border point
            if p.is_core(start, end):
                reg=p.get_core_region(start, end)
                if self not in reg:
                    reg.expand(self)
                    if self.first is None:
                        self.first = reg
            else:
                # p became a new core point after the addition of this point
                if p.is_dense(threshold, start, end):
                    # if p was a border point, we get all the regions 
                    # containing it and we merge them all.
                    # p becomes a core point in the new region and N(p) gets 
                    # added as border

                    if p.is_border(start, end):
                        big_region = NodeRegion.merge(
                            p.neighboring_regions(start, end), p
                        )

                        # only neighbors after the beginnig of the time frame
                        # not already there
                        for n in p.neighbors:
                            if n.time > big_region.start_context and n not in big_region:
                                big_region.expand(n)
                                # first region of a point, for region log
                                if n.first is None:
                                    n.first = big_region
                        p.add_core_region(big_region,start,end)
                    else:
                        new_region = LeafRegion(p) # TREE
                        new_region.start_context = start
                        for n in p.neighbors:
                            if n.time > new_region.start_context:
                                new_region.expand(n)
                                if n.first is None:
                                    n.first = new_region
                        # creation time and presence
                        new_region.c_time = p.time
                        new_region.c_pres = new_region.presence()

                        p.add_core_region(new_region,start,end)
                        p.first = new_region


    def get_core(self):
        return self.core

    def set_core(self,b):
        self.core=b

    def get_len_neighbors(self):
        return len(self.neighbors)

    def set_len_neighbors(self):
        self.len_neigh= len(self.neighbors)

    def get_density_rank(self):
        return self.density_rank

    def set_density_rank(self, r):
        self.density_rank= r





