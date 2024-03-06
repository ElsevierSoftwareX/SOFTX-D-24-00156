"""Feature implementation for the SEQSCAN algorithm."""

from .feature_point import FeaturePoint

class Feature(object):

	def __init__(self, fTime, lat, lon):
		"""Constructor.
		"""
		self.objectTime = fTime
		self.lat = lat
		self.lon = lon