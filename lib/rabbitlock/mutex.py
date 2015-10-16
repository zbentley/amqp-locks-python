import rabbitlock.connection
import pika


class _InternalMutex(rabbitlock.connection.SingleChannelConnection):
    def __init__(self, name, parameters, paranoid=True, release_on_destroy=False):
        self.name = name
        self.parameters = parameters
        self.paranoid = paranoid
        self._clear_held_locks()
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
    def clear_channel(self):
        self._clear_held_locks()
        super().clear_channel()

    def _publish(self, name=""):
        self.publish(
            exchange="",
            body="",
            routing_key=self.name + name,
            mandatory=True,
            properties=pika.BasicProperties(delivery_mode=1)
        )
        # TODO no route handling, confirmation success/failures

    def _ensure_mutex_acquired(self):
        success = False
        try:
            if self.paranoid:
                success = self._acquire_mutex()
            elif self._has_lock(0):
                success = self._publish()
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

    def _ensure_mutex_released(self):
        try:
            self.delete_queue(queue=self.name)
        except pika.exceptions.ConnectionClosed as e:
            try:
                self.clear_channel()
            except pika.exceptions.ConnectionClosed as e2:
                print("Destroy: got something that should be handled: " + repr(e2))
        finally:
            if self.paranoid:
                self.clear_channel()

    def __del__(self):
        if self.release_on_destroy:
            self._ensure_mutex_released()


class Mutex(_InternalMutex):

    def ensure_acquired(self):
        return self._ensure_mutex_acquired()

    def ensure_released(self):
        return self._ensure_mutex_released()