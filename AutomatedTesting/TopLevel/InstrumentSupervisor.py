import pyvisa
import os
import signal


def signal_handler(a, b):
    assert False


signal.signal(signal.SIGUSR1, signal_handler)


class InstrumentSupervisor():
    def __init__(self):
        """
        All test scripts should be implmented as a class which inherits this.
        Implements all the setup / cleanup and error handling

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self.instruments = []
        self.resourceManager = pyvisa.ResourceManager('@py')
        self.mainThread = os.getpid()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Shuts down all registered instruments

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        for x in self.instruments:
            self.free_resouce(x)

    def request_resources(self, instruments):
        """
        Initialises resources needed by test script

        Args:
            instruments list(BaseInstrument): instruments to setup

        Returns:
            None

        Raises:
            None
        """
        for x in instruments:
            x.initialise(self.resourceManager, self)
            self.instruments.append(x)

    def free_resouce(self, instrument):
        """
        Releases resources

        Args:
            instrument (BaseInstrument): Instrument to release
        Returns:
            None

        Raises:
            ValueError: if instrument is not already in use
        """
        if instrument not in self.instruments:
            raise ValueError

        instrument.cleanup()
        self.instruments.remove(instrument)

    def handle_instrument_error(self):
        """
        Called by monitoring thread if instrument has error while active.
        Passes signal to main thread indicating it should shutdown

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        os.kill(self.mainThread, signal.SIGUSR1)
