class Point:

    def __init__(self, lat, lon, timestamp, annotations=None):
        self.__lat = lat
        self.__lon = lon
        self.__ts = timestamp
        
        if annotations is None:
            self.__annotations = {}
        else:   
            self.__annotations = annotations.copy()

    def get_annotation(self, name):
        return self.__annotations[name]

    @property    
    def lat(self):
        return self.__lat

    @property    
    def lon(self):
        return self.__lon

    @property    
    def x(self):
        return self.__lon

    @property    
    def y(self):
        return self.__lat

    @property    
    def timestamp(self):
        return self.__ts
    
    @property    
    def annotations(self):
        return self.__annotations

    def copy(self):
       return Point(self.__lat, self.__lon, self.__ts, self.__annotations.copy()) 


    