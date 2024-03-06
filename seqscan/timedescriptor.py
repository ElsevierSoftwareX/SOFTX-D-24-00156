"""Time segment implementation for the SEQSCAN algorithm."""

from datetime import datetime, timedelta
from .simplerange import SimpleRange

class TimeDescriptor(object):
    """Ordered list of SimpleRange for a SEQSCAN Region."""

    def __init__(self, sr=None):
        """Initializes a new TimeDescriptor.
        
        Args:
            sr: a SimpleRange to be put into this TimeDescriptor, defaults to 
                None.
        """
        self.index = 0
        self.segment = [] if sr is None else [sr]
        
    def __repr__(self):
        return str(self.segment)
        
    # looks like a generator
    def _next(self):
        try:
            return self.segment[self.index]
        except IndexError:
            return None
        finally :
            self.index += 1
        
    def __add__(self, other):
        """TimeDescriptor addition."""
        return TimeDescriptor.union(self, other)
        
    @staticmethod
    def union(r1, r2):
        """Merges toghether two TimeDescriptor objects.
        
        r1 (TimeDescriptor) : the first time descriptor ==
        r2 (TimeDescriptor) : the second time descriptor
        """
        # sanity check
        if len(r1.segment) == 0:
            return r2
            
        if len(r2.segment) == 0:
            return r1
        
        d = TimeDescriptor() # the result
        
        # init
        r1.index = 0
        r2.index = 0

        one = r1.segment[0]
        two = r2.segment[0]
    
        if one.start <= two.start:
            start = one.start
            t_start = one.t_start
            n = one
            current = r2
            other = r1
        else:
            start = two.start
            t_start = two.t_start
            n = two
            current = r1
            other = r2

        other._next()
        
        next = current._next()
        
        while True:
            if next is None:
                d.segment.append(n)
                d.segment[len(d.segment):] = other.segment[other.index:]
                return d
                
            if next.start > n.stop + 1:
                d.segment.append(n)
                
                if other.index < len(other.segment):
                    p = other.segment[other.index]
                else:
                    d.segment.append(next)
                    d.segment[len(d.segment):] = current.segment[current.index:]
                    return d
    
                if next.start <= p.start:
                    start = next.start
                    t_start = next.t_start
                    
                    # pythonic swap
                    current, other = other, current
                    
                    n = next
                    next = current._next()
                else:
                    start = p.start
                    t_start = p.t_start
                    
                    n = p
                    other._next()
                    
            else:
                if next.stop > n.stop:
                    end = next.stop
                    t_end = next.t_stop
                    
                    # pythonic swap
                    current, other = other, current
                    n = SimpleRange(start, t_start, end, t_end)
                    
                    next = current._next()
                    
                else:
                    next = current._next()
        
    def add_simple_range(self, simple_range):
        """Adds simple_range to this TimeDescriptor."""
        
        t = TimeDescriptor(simple_range)
        TD = TimeDescriptor.union(self, t) # lots of memory wasted
        
        self.segment = TD.segment
        
    def presence(self):
        """Returns the sum of duration of SimpleRange in this TimeDescriptor."""
        return sum((sr.duration for sr in self.segment), timedelta(0))
        
    def duration(self):
        """Returns the duration, i.e. last timestamp - first timestamp."""
        return timedelta(0) if len(self.segment) == 0 else (
            self.segment[-1].t_stop - self.segment[0].t_start
        )
        
    def last(self):
        """Returns the last timestamp of this TimeDescriptor."""
        return self.segment[-1].t_stop
        
    def first(self):
        """Returns the first timestamp of this TimeDescriptor."""
        return self.segment[0].t_start