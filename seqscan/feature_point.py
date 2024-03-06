"""FeaturePoint implementation for the SEQSCAN algorithm."""

import utm
import json

with open('./config.json') as f:
    config = json.load(f)
CARTESIAN= config["is_cartesian"]

class FeaturePoint:
	array_rep = ()
	def __init__(self, lat=0.0, lon=0.0, cartesian=False):

		cartesian=CARTESIAN
		if not cartesian:
			coords = utm.from_latlon(lat,lon)
			self.x = coords[0]
			self.y = coords[1]
		else:
			self.x = lon
			self.y = lat

		self.lat = lat
		self.lon = lon 
		self.array_rep=(self.lat, self.lon)