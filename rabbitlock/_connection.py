import pika


class _SingleChannelConnection(object):
    def __init__(self, parameters):
        self._channel_internal = None
        self.parameters = parameters
        self._get_channel()

    def _get_channel(self):
        if self._channel_internal is not None:
            if not self._channel_internal.is_open or not self.connection.is_open:
                self.clear_channel()
        if self._channel_internal is None:
            self.connection = pika.BlockingConnection(self.parameters)
            self.set_channel(self.connection.channel())
        return self._channel_internal

    def _set_channel(self, channel):
        channel.confirm_delivery()
        self._channel_internal = channel
        return channel

    def _clear_channel(self):
        self._channel_internal = None
        if self._channel_internal.is_open:
            try:
                self._channel_internal.close()
            except:
                pass
        if self.connection.is_open:
            try:
                self.connection.close()
            except pika.exceptions.ConnectionClosed as e:
                if e.args[0] != 302:  # CONNECTION_FORCED
                    raise

    _channel = property(_get_channel, _set_channel, _clear_channel)
