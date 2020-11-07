from multiprocessing import Process, Event


class ProcessWithCleanStop():

    def __init__(self, **kwargs):
        self._event = Event()
        self._process = Process(args=(self._event,), daemon=True, **kwargs)

    def terminate(self):
        self._event.set()
        self._process.join()

    def start(self):
        self._process.start()

