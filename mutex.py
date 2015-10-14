from single_channel_connection import SingleChannelConnection

class Mutex(SingleChannelConnection):
	def __init__(self, name, parameters, paranoid=True):
		self.name = name
		self.parameters = parameters
		self.paranoid = paranoid
		super().__init__(parameters)