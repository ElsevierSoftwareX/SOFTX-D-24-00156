"""SimpleRange implementation for the SEQSCAN algorithm."""

from functools import total_ordering
from datetime import datetime, timedelta

@total_ordering
class SimpleRange(object):
    """Interval between two events, e.g. two consecutive positions of an animal.
    
    Each event is denoted by its id and timestamp: ids are used to merge 
    consecutive events whereas timestamps are used to compute their length.
        
    SimpleRange are (totally) ordered by sorting the (t_start, t_stop) couples.
    """
    
    def __init__(self, start, t_start, stop=None, t_stop=None):
        """Initializes a SimpleRange.
        
        Args:
            start (int) : id of the first event.
            t_start (datetime) : timestamp of the first event.
            stop (int, optional) : id of the second event, defaults to None.
            t_stop (datetime, optional) : timestamp of the second event, 
                defaults to None.
            
        Note:
            if either stop is None OR t_stop is None, _BOTH_ are assumed to be 
            the same as start and t_start, i.e. the interval reduces to a single 
            point.
        
        Raises:
            ValueError if start (t_start) is greater than stop (t_stop).
        """
        # legality check
        if stop is not None and start > stop:
            raise ValueError('start id %d follows end id %d' % (start, stop))
        
        if t_stop is not None and t_start > t_stop:
            raise ValueError('start timestamp %s follows end timestamp %s' % 
                (t_start, t_stop)
            )
        
        self.start = start
        self.t_start = t_start
        
        self.stop = stop if stop is not None and t_stop is not None else start
        self.t_stop = (
            t_stop if stop is not None and t_stop is not None else t_start
        )
        
        self.duration = self.t_stop - self.t_start          # aggregated value
        
    # Total ordering.
    def __eq__(self, other):
        if not isinstance(other, SimpleRange):
            raise TypeError("%s is not a SimpleRange." % other)
        return (self.t_start, self.t_stop) == (other.t_start, other.t_stop)
        
    def __lt__(self, other):
        if not isinstance(other, SimpleRange):
            raise TypeError("%s is not a SimpleRange." % other)
        return (self.t_start, self.t_stop) < (other.t_start, other.t_stop)
        
    # Addition
    def disjoint(self, other):
        """True iif self _PRECEDES_ other (or v/v) in Allen's interval algebra.
        
        Raises:
            TypeError if other is not a SimpleRange.
            
        Note:
            we are using integers to define intervals, so we say that 
            [a, i] _MEETS_ [i+1, b]
        """
        if not isinstance(other, SimpleRange):
            raise TypeError("%s is not a SimpleRange object." % other)
        return self.stop + 1 < other.start or other.stop + 1 < self.start
        
    def __add__(self, other):
        """Adds two non-disjoint SimpleRange.
        
        If [a, b] and [c, d] are non disjoint intervals, their sum is [i, j] 
        where i = min(a, c) and j = max(b, d).
           
        Raises:
            TypeError if other is not a SimpleRange.
            ValueError if other is disjoint from this object.
        """
        if not isinstance(other, SimpleRange):
            raise TypeError("%s is not a SimpleRange." % other)
            
        if self.disjoint(other):
            raise ValueError('%s and %s are disjoint.' % (self, other))
            
        i = min(self.start, other.start)
        t_i = min(self.t_start, other.t_start)
        j = max(self.stop, other.stop)
        t_j = max(self.t_stop, other.t_stop)
        
        return SimpleRange(i, t_i, j, t_j)
     
    # toString()
    def __repr__(self):
        return '(%d, %s, %d, %s)' % (
            self.start, self.t_start, self.stop, self.t_stop
        )
        
    def __contains__(self, index):
        """True if self.start <= index self.stop."""
        return self.start <= index <= self.stop