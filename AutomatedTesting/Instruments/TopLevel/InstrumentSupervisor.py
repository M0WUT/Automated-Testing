import logging
import os
import signal
import sys

import pyvisa


class InstrumentConnectionError(Exception):
    pass


class InstrumentSupervisor:
    def __init__(self, loggingLevel=logging.WARNING):
        """
        Implements all the setup / cleanup and error handling of instruments

        Args:
            loggingLevel: level of detail which should be logged

        Returns:
            None

        Raises:
            None
        """
        self.instruments = []
        logging.basicConfig(
            format="%(levelname)s: %(asctime)s %(message)s", level=loggingLevel
        )
        self.resourceManager = pyvisa.ResourceManager("@py")
        self.mainThread = os.getpid()
        self.shutdown = False
        signal.signal(signal.SIGUSR1, self.signal_handler)

    def __enter__(self):
        # Need this to also support being in a context
        # manager for some of the unit tests
        return self

    def __exit__(self, *args, **kwargs):
        self.cleanup()

    def cleanup(self):
        """
        Shuts down all registered instruments

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        while self.instruments != []:
            self.free_resource(self.instruments[0])

    def signal_handler(self, *args, **kwargs):
        """
        Catches all signals indicating instrument faults
        Shutdown is long enough that same error may be
        thrown during shutdown so only responds to the first
        one

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        if not self.shutdown:
            self.shutdown = True
            self.cleanup()
            sys.exit(1)
        else:
            pass

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
            try:
                x.initialise(self.resourceManager, self)
                self.instruments.append(x)
            except InstrumentConnectionError:
                raise InstrumentConnectionError(
                    f"Failed to connect to {x.name} at {x.address}. "
                    f"Available resources: "
                    f"{self.resourceManager.list_resources()}"
                )

    def free_resource(self, instrument):
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
        Passes signal to main thread on the first fault encountered

        Args:
           None

        Returns:
            None

        Raises:
            None
        """
        os.kill(self.mainThread, signal.SIGUSR1)
