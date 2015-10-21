import rabbitlock.mutex
import pika
import time
import random


class Semaphore(rabbitlock.mutex._InternalMutex):
    slept = False

    def _acquire_semaphore(self):
        eligible = 1
        while self._semaphore_exists(eligible):
            if self._ping("-B-%d" % eligible):
                eligible += 1
            else: # Slot is available
                break
        else:
            print("Ran out of sems")
            return False

        try:
            self._channel.queue_declare(
                queue="%s-B-%d" % (self.name, eligible),
                durable=False,
                exclusive=True,
                auto_delete=False,
                arguments={
                    "x-max-length": 0,
                }
            )
            self._add_held_lock(eligible)
        except pika.exceptions.ChannelClosed as e:
            if e.args[0] != 405:  # RESOURCE_LOCKED; we didn't get the lock
                raise
            print("Race condition victim!")
            # Make the race condition marginally less probable by adding a random
            # time skew to a given Lock instance's spin interval. This is an
            # optimization for the case where many connections try to
            # get locks at about the same time. It's totally optional.
            if self.paranoid and not self.slept:
                self.slept = True
                time.sleep(10.0 / random.randrange(75))
            return self._acquire_semaphore()
        else:
            # In paranoid mode, re-verify lock ownership. This is done since
            # queue_declare is an operation that consumes more time than a
            # publish, so there's a wider window than usual in which the lock
            # could have been decremented.
            if self.paranoid:
                return self._verify_semaphore_held()
            else:
                return eligible

    def _held_semaphore(self):
        for key in self._locks_held.keys():
            if key != 0:
                return key
        return None

    def _semaphore_exists(self, num):
        return num > 0 and self._ping("-A-%d" % num)

    def _verify_semaphore_held(self):
        if not self._semaphore_exists(self._held_semaphore()):
            self.release_semaphore()
        return self._held_semaphore()

    def _get_max_semaphore(self, overshoot=0):
        num = 1
        while self._semaphore_exists(num):
            num += 1
        return num - 1 + overshoot

    def _decrement_semaphore(self, max, count):
        for num in range(max, max - count, -1):
            print("Deleting %d" % num)
            self._channel.queue_delete("%s-A-%d" % (self.name, num))
            if num == self._held_semaphore():
                self.ensure_semaphore_released()

    def _increment_semaphore(self, max, count):
        for num in range(1, count + 1):
            self._channel.queue_declare(
                queue="%s-A-%d" % (self.name, max + num),
                durable=False,
                arguments={
                    "x-max-length": 0,
                }
            )

    def adjust_semaphore(self, num):
        success = False
        try:
            if self._ensure_mutex_acquired():
                max = self._get_max_semaphore()
                if num > 0:
                    self._increment_semaphore(max, num)
                elif max > 0: # Don't bother decrementing if there are no slots.
                    self._decrement_semaphore(max, abs(num))
                success = True
        finally:
            self._ensure_mutex_released()
        return success

    def ensure_semaphore_destroyed(self):
        try:
            if self._ensure_mutex_acquired():
                size = self._get_max_semaphore(overshoot=100) # TODO remove
                self._decrement_semaphore(size, size)
        finally:
            self._ensure_mutex_released()

    def ensure_semaphore_held(self):
        if self._held_semaphore() is not None:
            return self._verify_semaphore_held()
        else:
            return self._acquire_semaphore()

    def ensure_semaphore_released(self):
        num = self._held_semaphore()
        self._remove_held_lock(num)
        try:
            self._channel.queue_delete("%s-B-%d" % (self.name, num))
        finally:
            if self.paranoid:
                self._clear_channel()

    def __del__(self):
        if self.release_on_destroy:
            self.ensure_semaphore_released()
