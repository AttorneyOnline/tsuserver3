class Evidence:
	def __init__(self, name, desc, image):
		self.name = name
		self.desc = desc
		self.image = image

	def set_name(self, name):
		self.name = name

	def set_desc(self, desc):
		self.desc = desc

	def set_image(self, image):
		self.image = image

	def to_string(self):
		sequence = (self.name, self.desc, self.image)
		return '&'.join(sequence)