"""Rectangle implementation for the SEQSCAN algorithm."""

class Rectangle(object):
	def __init__(self, p1, p2, xmin=0, xmax=0, ymin=0, ymax=0):
		if ((p1 is not None) and (p2 is not None)):
			self.set(p1,p2)
		else:
			self.xmin = xmin
			self.xmax = xmax
			self.ymin = ymin
			self.ymax = ymax
			self.normalize()
		
	def set(self, p1, p2):
		self.xmin = p1.x
		self.xmax = p2.x
		self.ymin = p1.y
		self.ymax = p2.y
		self.normalize()
	
	def swap(self, x1, x2):
		x1, x2 = x2, x1
	
	def normalize(self):
		if self.xmin > self.xmax :
			self.swap( self.xmin, self.xmax )
		
		if self.ymin > self.ymax :
			self.swap( self.ymin, self.ymax )
	

	def grow(self, delta):
		self.xmin -= delta
		self.xmax += delta
		self.ymin -= delta
		self.ymax += delta

	def include(self, p):
		if p.x < self.xmin :
			self.xmin = p.x
		elif p.x > self.xmax :
			self.xmax = p.x
		if p.y < self.ymin :
			self.ymin = p.y
		if p.y > self.ymax :
			self.ymax = p.y

	def buffer(self, width):
		self.xmin -= width
		self.ymin -= width
		self.xmax += width
		self.ymax += width
		return self

	def intersect(self, rect):
		intersection = type('Rectangle', (object,), {})()
		#If they don't actually intersect an empty Rectangle should be returned
		if ( rect is None or self.intersects( rect )==False ):
			return intersection

		intersection.xmin = ( self.xmin if self.xmin > rect.xmin else rect.xmin )
		intersection.xmax = ( self.xmax if self.xmax < rect.xmax else rect.xmax )
		intersection.ymin = ( self.ymin if self.ymin > rect.ymin else rect.ymin )
		intersection.ymax = ( self.ymax if self.ymax < rect.ymax else rect.ymax )
		return intersection

	def intersects(self, rect):
		x1 = ( self.xmin if self.xmin > rect.xmin else rect.xmin )
		x2 = ( self.xmax if self.xmax < rect.xmax else rect.xmax )
		if ( x1 > x2 ):
			return False

		y1 = ( self.ymin if self.ymin > rect.ymin else rect.ymin )
		y2 = ( self.ymax if self.ymax < rect.ymax else rect.ymax )
		if ( y1 > y2 ):
			return False
			
		return True

	def contains(self, rect):
		return ( rect.xmin >= self.xmin and rect.xmax <= self.xmax and rect.ymin >= self.ymin and rect.ymax <= self.ymax )

	def contains_point(self, p):
		return (self.xmin <= p.x and p.x <= self.xmax and self.ymin <= p.y and p.y <= self.ymax)

	def combineExtentWithRect(self, rect):
		self.xmin = ( self.xmin if (self.xmin < rect.xmin ) else rect.xmin )
		self.xmax = ( self.xmax if (self.xmax > rect.xmax ) else rect.xmax )
		self.ymin = ( self.ymin if (self.ymin < rect.ymin ) else rect.ymin )
		self.ymax = ( self.ymax if (self.ymax > rect.ymax ) else rect.ymax )

	def combineExtentWith(self, x, y):
		self.xmin = ( self.xmin if ( self.xmin < x ) else x )
		self.xmax = ( self.xmax if ( self.xmax > x ) else x )
		self.ymin = ( self.ymin if ( self.ymin < y ) else y )
		self.ymax = ( self.ymax if ( self.ymax > y ) else y )

	def isEmpty(self):
		return (self.xmax <= self.xmin or self.ymax <= self.ymin)

	def invert(self):
		tmp = self.xmin
		self.xmin = self.ymin
		self.ymin = tmp
		tmp = self.xmax
		self.xmax = self.ymax
		self.ymax = tmp
	