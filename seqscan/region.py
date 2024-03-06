"""Region implementation for the SEQSCAN algorithm."""


# Standard modules
from __future__ import division
from collections import defaultdict
from datetime import datetime, timedelta

# My modules
from .simplerange import SimpleRange
from .timedescriptor import TimeDescriptor

from .rectangle import Rectangle

class Region(object):
    """Region implementation for the SEQSCAN algorithm."""
    
    counter = 0             # instance counter / id generator
    
    # ALL these fields MUST be (re)set 
    # by the Scanner when processing a new animal
    threshold = None        # persistence threshold
    log = None              # (dense) region log
    
    phase = None    # phase flag
    expansion_log   = None    # set of regions created during expansion phase
    look_up_log     = None    # set of regions created during look_up phase
    expansion_noise = None    # set of noise points visited during expansion
    look_up_noise   = None    # set of noise points visite during look_up
    
    # phase constants
    EXPANSION = 0
    LOOK_UP   = 1
    
    
    def __init__(self, point):
        """Creates an empty region for the given animal.
        
        Args:
            point (Point) : first point of the region
            
        Note:
            ids are generated using the class counter: this technique is NOT 
            thread-safe.
        """
        self.id   = Region.counter      # object id
        self.next = self                # reference to a bigger region
        self.hook = self                # faster reference to a bigger Region
        self.level = 0                  # default hierarchy level
        self.time = TimeDescriptor()    # time descriptor



        self.start_context = datetime.max #the time context of the region
        # Points contained in the region, for multiple purposes
        self.points = set([point])
        
        # bounding box
        self.box = Rectangle(point.geometry, point.geometry)
        
        self.noise = 0                  # counter of excursion points
        self.persistent = False         # aggregate persistence flag
        
        self.c_time = None              # creation timestamp
        self.c_pres = None              # presence at creation
        
        # Increments the static counter
        Region.counter += 1
        
        # Adds this region to the logs
        Region.log.append(self)
        if Region.phase == Region.EXPANSION:
            Region.expansion_log.add(self)
            Region.expansion_noise.discard(point)
        else:
            Region.look_up_log.add(self)
            Region.look_up_noise.discard(point)
        
    def __repr__(self):
        return "( ptrs:(%d -> %d) time:%s)" % (
            self.id,
            self.next.id, 
            self.time
        )
        

        
    def walk(self):
        """Returns the final region that this region is part of.
           
           When a new region is created, its final region is the region itself;
           when two (or more) regions merge together their final region becomes
           the (newly created) result of the merge operation. 
           
           Operation involving regions outside of this class (as well as static 
           or class methods) _SHOULD_ call walk() to get access to the final 
           region.
        """
        # Beware of stack smashing problems arising when dealing with long 
        # chains of pointers.
        # return self if self is self.next else self.next.walk()
        
        # Safer iterative way.
        

        while self is not self.hook:
            self = self.hook
        if self is not self.next:
            raise ValueError("region and next are different at the end of walk")



        return self
        
    def __contains__(self, point):
        """True if this Region contains the specified Point.
        
        Args:
            point (Point): a MigrO.seqscan.Point object
            
        Note:
            instead of a time consuming TimeDescriptor scan, this method checks 
            membership in a set of Points
        """
        return point in self.points
        
    def expand(self, point):
        """Adds a new Point to this Region.
        
        Args:
            point (Point) : a MigrO.seqscan.Point object
        """
        self.time.add_simple_range(SimpleRange(point.id, point.time))
        
        # persistence update
        self.persistent |= self.time.presence() >= Region.threshold
        
        # cache update
        self.points.add(point)
        
        # noise update
        if Region.phase == Region.EXPANSION:
            Region.expansion_noise.discard(point)
        else:
            Region.look_up_noise.discard(point)
        
        # bounding box update
        self.box.combineExtentWith(point.geometry.x, point.geometry.y)
        
    @staticmethod
    def merge(region_set, point):
        """Merges all the Regions in the set to create a new one.
        
        Args:
            point (Point) : the 'common point' between regions
        """
        
        # Sanity checks
        if len(region_set) < 1:
            raise ValueError("Merging an empty set of Regions", region_set)
        
        # Gets the set of the final regions
        finals = set(r.walk() for r in region_set)

        if len(finals) > 1:
            result = NodeRegion(point)
            for region in finals:
                # print "i amasasasasasaasas"
                result.time += region.time               # time segment update
                result.points |= region.points           # cache update
                result.box.combineExtentWithRect(region.box) # bounding box update
                result.children.add(region)              # pointer update
                region.next = result                     # pointer update
                if Region.phase == Region.EXPANSION:
                    Region.expansion_log.discard(region)
                else:
                    Region.look_up_log.discard(region)




            for region in finals | region_set:
                region.hook = result  # pointer update


            # level update
            result.level = 1 + max(region.level for region in finals)
                
            # persistence update
            result.persistent = (any(r.persistent for r in finals) or 
                result.presence() >= Region.threshold
            )

            result.start_context = finals.pop().start_context

            return result

        # only one final region in the set
        else:
            result = finals.pop()

        # Single return statement
        return result
        
    # retrieves all the points in the square
    def query(self, square, result):
        """Abstract method."""
        pass
        
    def presence(self):
        """Returns the presence."""
        return self.time.presence()
        
    def duration(self):
        """Returns the duration."""
        return self.time.duration()
        
    def ratio(self):
        """Returns the presence / duration ratio."""
        return self.presence().total_seconds() / self.duration().total_seconds()
        
    def is_persistent(self):
        """Returns the (aggregate) persistence flag."""
        return self.persistent
        
    def last_timestamp(self):
        """Returns the last timestamp of this Region."""
        return self.time.last()
        
    def first_timestamp(self):
        """Returns the first timestamp of this Region."""
        return self.time.segment[0].t_start
        
    def mean_timestamp(self):
        """Returns the mean timestamp of this Region."""
        f = self.time.first()
        l = self.time.last()
        return f + ((l - f) // 2)
        
    def in_time_frame(self, start, end):
        """True if this Region is inside the specified time frame.
        
        Args:
            start (datetime): begin timestamp of the time frame
            end (datetime): end timestamp of the time frame
        """
        return start < self.time.segment[0].t_start


# leaves of the region tree structure
class LeafRegion(Region):
    
    def __init__(self, point):
        super(LeafRegion, self).__init__( point)
        
    def query(self, square, result):
        """Adds to the result all the points contained into the square.
        
        Args:
            square (Rectangle): a Rectangle
            result (set of Point): a set of Point
        """
        if self.box.intersects(square):
            result |= set(p for p in self.points if square.contains_point(p.geometry))
        

# nodes of the region tree structure
class NodeRegion(Region):
    
    def __init__(self, point):
        super(NodeRegion, self).__init__( point)
        
        self.more_points = set([point]) # set of points added after the fusion
        self.children    = set() # set of pointers to lower level
        
    def expand(self, point):
        """Adds a new Point to this Region.
        
        Args:
            point (Point) : a MigrO.seqscan.Point object
        """

        self.time.add_simple_range(SimpleRange(point.id, point.time))

        # persistence update
        self.persistent |= self.time.presence() >= Region.threshold
        
        # cache update
        self.points.add(point)          # for backward compatibility and look up
        self.more_points.add(point)     # for query
        
        # noise update
        if Region.phase == Region.EXPANSION:
            Region.expansion_noise.discard(point)
        else:
            Region.look_up_noise.discard(point)
        
        # bounding box update
        self.box.combineExtentWith(point.geometry.x, point.geometry.y)
        
    def query(self, square, result):
        """Adds to the result all the points contained into the square.
        
        1. retrieves all points contained into the expansion set (more_points)
        2. queries each child
            
        Args:
            square (Rectangle): a Rectangle
            result (set of Point): a set of Point
            
        Note:
            explores the sub-trees
        """
#        if self.box.intersects(square):
#            result |= set(
#                p for p in self.more_points if square.contains_point(p.geometry)
#            )
#            for child in self.children:
#                if child.box.intersects(square):
#                    child.query(square, result)

        # iterative way
        if self.box.intersects(square):
            queue = [self]
            while queue:
                r = queue.pop()
                if type(r) == LeafRegion:
                    r.query(square, result)
                else:
                    result |= set(p for p 
                        in r.more_points 
                        if square.contains_point(p.geometry)
                    )
                    queue += (child for child 
                        in r.children
                        if child.box.intersects(square)
                    )
        
