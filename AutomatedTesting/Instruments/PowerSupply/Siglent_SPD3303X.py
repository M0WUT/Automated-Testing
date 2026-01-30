# Standard imports
import logging
from time import sleep

from pyvisa import ResourceManager

# Third party imports
from AutomatedTesting.Instruments.PowerSupply.PowerSupply import (
    PowerSupply,
    PowerSupplyChannel,
)

# Local imports


class SiglentSPD3303X(PowerSupply):
    # Bit masks for status byte
    CHANNEL1_MODE_BIT = 0
    CHANNEL2_MODE_BIT = 1
    MODE_LSB = 2
    MODE_MSB = 3
    CHANNEL1_STATUS = 4
    CHANNEL2_STATUS = 5
    TIMER1_STATUS = 6
    TIMER2_STATUS = 7
    CHANNEL1_DISPLAY = 8
    CHANNEL2_DISPLAY = 9

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
            channels=[
                PowerSupplyChannel(
                    channel_num=1,
                    instrument=self,
                    logging_level=logging_level,
                    min_voltage=0,
                    max_voltage=32,
                    min_current=0,
                    max_current=3.2,
                ),
                PowerSupplyChannel(
                    channel_num=2,
                    instrument=self,
                    logging_level=logging_level,
                    min_voltage=0,
                    max_voltage=32,
                    min_current=0,
                    max_current=3.2,
                ),
            ],
            logging_level=logging_level,
            *args,
            **kwargs,
        )

    def _set_remote_control(self) -> None:
        pass

    def _set_local_control(self) -> None:
        pass

    def _get_channel_errors(self, channel_num: int) -> list[tuple[int, str]]:
        status = self._get_status_byte()

        if (channel_num == 1 and status[self.CHANNEL1_MODE_BIT] == "1") or (
            channel_num == 2 and status[self.CHANNEL2_MODE_BIT] == "1"
        ):
            return [(1, "Overcurrent")]  # pragma: no cover
        else:
            return []

    def _set_channel_voltage(self, channel_num: int, voltage: float) -> None:
        self._write(f"CH{channel_num}:VOLT {round(voltage, 3)}")

    def _get_channel_voltage(self, channel_num: int) -> float:
        return float(self._query(f"CH{channel_num}:VOLT?"))

    def _measure_channel_voltage(self, channel_num: int) -> float:
        return float(self._query(f"MEAS:VOLT? CH{channel_num}"))

    def _set_channel_current_limit(self, channel_num: int, current: float) -> None:
        self._write(f"CH{channel_num}:CURR {round(current, 3)}")

    def _get_channel_current_limit(self, channel_num: int) -> float:
        return float(self._query(f"CH{channel_num}:CURR?"))

    def _measure_channel_current(self, channel_num: int) -> float:
        return float(self._query(f"MEAS:CURR? CH{channel_num}"))

    def _set_channel_output_enabled_state(
        self, channel_num: int, enabled: bool
    ) -> None:
        self._write(f"OUTP CH{channel_num},{'ON' if enabled else 'OFF'}")
        if enabled:
            sleep(1)

    def _get_channel_output_enabled_state(self, channel_num: int) -> bool:
        status = self._get_status_byte()
        if channel_num == 1:
            return status[self.CHANNEL1_STATUS] == "1"
        else:
            return status[self.CHANNEL2_STATUS] == "1"

    def _get_status_byte(self) -> str:
        # Get status byte and convert to string in reverse
        # order so status[0] = bit 0
        response = self._query("SYST:STATUS?")
        status = int(response, 0)
        status = format(status, "010b")[::-1]
        return status
