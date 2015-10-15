import rabbitlock.connection
import pika

class Mutex(rabbitlock.connection.SingleChannelConnection):
	def __init__(self, name, parameters, paranoid=True, release_on_destroy=False):
		self.name = name
		self.parameters = parameters
		self.paranoid = paranoid
		self.locks_held = {}
		self.release_on_destroy = release_on_destroy
		super().__init__(parameters)


	def _acquire_mutex(self):
		self.declare_queue(
			queue=self.name,
			durable=False,
			exclusive=True,
			auto_delete=False,
			arguments={
				"x-max-length": 0,
			}
		)
		self.locks_held[self.name] = True

	# Clear locks on reset
	def clear_channel(self):
		self.locks_held = {}
		super().clear_channel()

	def ensure_acquired(self):
		success = False
		try:
			if self.paranoid:
				self._acquire_mutex()
			elif self.locks_held[self.name]:
				self.publish(
					exchange="",
					body="",
					routing_key=self.name,
					mandatory = True,
					properties=pika.BasicProperties(delivery_mode=1)
				)
			else:
				self._acquire_mutex()
			success = True
		except pika.exceptions.ConnectionClosed as e:
			if e.args[0] == 302: # CONNECTION_FORCED
				self.ensure_released()
				self._acquire_mutex()
				success = True
			else:
				raise
		except pika.exceptions.ChannelClosed as e:
			if e.args[0] != 405: # RESOURCE_LOCKED; we didn't get the lock
				raise
		return success

	def ensure_released(self):
		try:
			self.delete_queue(queue=self.name)
		except pika.exceptions.ConnectionClosed as e:
			try:
				self.clear_channel()
			except pika.exceptions.ConnectionClosed as e2:
			 	print("Destroy: got something that should be handled: " + repr(e2))


	def __del__(self):
		if self.release_on_destroy:
			self.ensure_released()