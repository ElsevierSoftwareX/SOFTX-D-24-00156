class Stop():

    def __init__(self,stop_id, start_time, end_time, centroid_x, centroid_y, tag_id=None ):
        self.stop_id=stop_id
        self.centroid_x=centroid_x
        self.centroid_y=centroid_y
        self.start_time=start_time
        self.end_time=end_time
        self.tag_id=tag_id
