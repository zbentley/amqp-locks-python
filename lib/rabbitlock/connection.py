import pika


class SingleChannelConnection(object):
    def __init__(self, parameters):
        self._channel = None
        self.parameters = parameters
        self.get_channel()

    def get_channel(self):
        if self._channel is not None:
            if not self._channel.is_open or not self.connection.is_open:
                self.clear_channel()
        if self._channel is None:
            self.connection = pika.BlockingConnection(self.parameters)
            self.set_channel(self.connection.channel())
        return self._channel

    def set_channel(self, channel):
        channel.confirm_delivery()
        self._channel = channel
        return channel

    def clear_channel(self):
        self._channel = None
        if self._channel.is_open:
            try:
                self._channel.close()
            except:
                pass
        if self.connection.is_open:
            try:
                self.connection.close()
            except pika.exceptions.ConnectionClosed as e:
                if e.args[0] != 302:  # CONNECTION_FORCED
                    raise

    channel = property(get_channel, set_channel, clear_channel)

    def publish(self, *args, **kw):
        return self.channel.basic_publish(*args, **kw)

    def declare_queue(self, *args, **kw):
        return self.channel.queue_declare(*args, **kw)

    def delete_queue(self, *args, **kw):
        return self.channel.queue_delete(*args, **kw)
