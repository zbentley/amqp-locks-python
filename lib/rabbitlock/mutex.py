import rabbitlock._mutex


class Mutex(rabbitlock._mutex._InternalMutex):

    def ensure_acquired(self):
        return self._ensure_mutex_acquired()

    def ensure_released(self):
        return self._ensure_mutex_released()