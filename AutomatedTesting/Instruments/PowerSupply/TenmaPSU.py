# Standard imports
import logging
from time import sleep
from typing import Optional

# Third party imports
from pyvisa import ResourceManager, VisaIOError

# Local imports
from AutomatedTesting.Instruments.PowerSupply.PowerSupply import (
    PowerSupply,
    PowerSupplyChannel,
)


class TenmaGeneric(PowerSupply):
    def __init__(
        self,
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        channels: list[PowerSupplyChannel],
        logging_level: int,
        *args,
        **kwargs,
    ):
        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            expected_idn_response=expected_idn_response,
            name=name,
            verify=verify,
            logging_level=logging_level,
            channels=channels,
            timeout=500,
            *args,
            **kwargs,
        )

    def _set_remote_control(self) -> None:
        pass

    def _set_local_control(self) -> None:
        pass

    def _get_channel_errors(self, channel_num: int) -> list[tuple[int, str]]:
        if self._get_status_byte() == 0:
            error_str = (
                f"PSU: {self.name}, "
                f"Channel {self.channels[channel_num - 1].name} "
                "is current limiting"
            )
            logging.error(error_str)
            return [(1, error_str)]
        else:
            return []

    def _set_channel_voltage(self, channel_num: int, voltage: float) -> None:
        self._write(f"VSET{channel_num}:{round(voltage, 2)}")

    def _get_channel_voltage(self, channel_num: int) -> float:
        return float(self._query_bytes(f"VSET{channel_num}?", 5))

    def _measure_channel_voltage(self, channel_num: int) -> float:
        return float(self._query_bytes(f"VOUT{channel_num}?", 5))

    def _set_channel_current_limit(self, channel_num: int, current: float) -> None:
        self._write(f"ISET{channel_num}:{round(current, 3)}")

    def _get_channel_current_limit(self, channel_num: int) -> float:
        return float(self._query_bytes(f"ISET{channel_num}?", 5))

    def _measure_channel_current(self, channel_num: int) -> float:
        return float(self._query_bytes(f"IOUT{channel_num}?", 5))

    def _set_channel_output_enabled_state(
        self, channel_num: int, enabled: bool
    ) -> None:
        self._write(f"OUT{1 if enabled else 0}")
        if enabled:
            sleep(1)

    def _get_channel_output_enabled_state(self, channel_num: int) -> bool:
        status = self._get_status_byte()
        return bool(status & 1 << 6)

    #############################################
    # Override of already implemented functions #
    #############################################

    def reset(self) -> None:
        # No reset functionality
        pass

    def _write(self, command: str, acquire_lock: bool = True) -> None:
        super()._write(command, acquire_lock)
        sleep(0.1)  # Super important - do not delete

    def _read(
        self, acquire_lock: bool = True, timeout_s: Optional[float] = None
    ) -> str:
        if acquire_lock:
            self.lock.acquire()
        try:
            old_timeout = self.dev.timeout
            if timeout_s:
                self.dev.timeout = timeout_s * 1000
            return_string = ""
            while True:
                try:
                    return_string += self._read_bytes(1)
                except VisaIOError:
                    break
        finally:
            self.dev.timeout = old_timeout
            if acquire_lock:
                self.lock.release()

        return_string = return_string.strip()
        self.logger.debug(f"RCVD: {return_string}")
        return return_string

    def _read_bytes(self, num_bytes: int) -> str:
        # Reads data from PSU as it's infernal with no termination
        return_string = self.dev.read_bytes(num_bytes + 1).decode("utf-8")
        assert return_string
        sleep(0.1)  # Super important - do not delete
        return return_string

    def _query_bytes(self, command: str, num_bytes: int) -> bytes:
        try:
            self.lock.acquire()
            self._write(command, acquire_lock=False)
            return self._read_bytes(num_bytes).strip()
        finally:
            self.lock.release()

    def _get_status_byte(self) -> int:
        # Get status byte and convert to string in reverse
        # order so status[0] = bit 0
        return ord(self._query_bytes("STATUS?", 1))

    def get_instrument_errors(self):
        return []


class Tenma722535(TenmaGeneric):
    def __init__(
        self,
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        logging_level: int,
        *args,
        **kwargs,
    ):
        self.name = name
        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            logging_level=logging_level,
            channels=[
                PowerSupplyChannel(
                    channel_num=1,
                    instrument=self,
                    logging_level=logging_level,
                    min_voltage=0,
                    max_voltage=30,
                    min_current=0,
                    max_current=3,
                )
            ],
            *args,
            **kwargs,
        )


class Tenma722940(TenmaGeneric):
    def __init__(
        self,
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        logging_level: int,
        *args,
        **kwargs,
    ):
        self.name = name
        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            logging_level=logging_level,
            channels=[
                PowerSupplyChannel(
                    channel_num=1,
                    instrument=self,
                    logging_level=logging_level,
                    min_voltage=0,
                    max_voltage=60,
                    min_current=0,
                    max_current=3,
                )
            ],
            *args,
            **kwargs,
        )
