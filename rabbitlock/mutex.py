import rabbitlock._connection
import pika


class _InternalMutex(rabbitlock._connection._SingleChannelConnection):
    def __init__(self, name, parameters, paranoid=True, release_on_destroy=False):
        self.name = name
        self.parameters = parameters
        self.paranoid = paranoid
        self._clear_held_locks()
        self.release_on_destroy = release_on_destroy
        super().__init__(parameters)

    def _acquire_mutex(self):
        self._channel.queue_declare(
            queue=self.name,
            durable=False,
            exclusive=True,
            auto_delete=False,
            arguments={
                "x-max-length": 0,
            }
        )
        self._add_held_lock(0)
        return True

    def _add_held_lock(self, num=0):
        self.locks_held[num] = True

    def _remove_held_lock(self, num=0):
        del (self.locks_held[num])

    def _clear_held_locks(self):
        self.locks_held = {}

    def _has_lock(self, num=0):
        return num in self.locks_held

    # Clear locks on reset
    def _clear_channel(self):
        self._clear_held_locks()
        super()._clear_channel()

    def _ensure_mutex_acquired(self):
        success = False
        try:
            if self.paranoid:
                success = self._acquire_mutex()
            elif self._has_lock(0):
                success = self._ping()
            else:
                success = self._acquire_mutex()
        except pika.exceptions.ConnectionClosed as e:
            if e.args[0] == 302:  # CONNECTION_FORCED
                self.ensure_released()
                self._acquire_mutex()
                success = True
            else:
                raise
        except pika.exceptions.ChannelClosed as e:
            if e.args[0] != 405:  # RESOURCE_LOCKED; we didn't get the lock
                raise
        return success

    def _ping(self, name=""):
        self._channel.basic_publish(
            exchange="",
            body="",
            routing_key=self.name + name,
            mandatory=True,
            properties=pika.BasicProperties(delivery_mode=1)
        )
        # TODO no route handling, confirmation success/failures

    def _ensure_mutex_released(self):
        try:
            self._channel.queue_delete(queue=self.name)
        except pika.exceptions.ConnectionClosed as e:
            try:
                self._clear_channel()
            except pika.exceptions.ConnectionClosed as e2:
                print("Destroy: got something that should be handled: " + repr(e2))
        finally:
            if self.paranoid:
                self._clear_channel()

    def __del__(self):
        if self.release_on_destroy:
            self._ensure_mutex_released()


class Mutex(_InternalMutex):
    ensure_acquired = _InternalMutex._ensure_mutex_acquired
    ensure_released = _InternalMutex._ensure_mutex_released
