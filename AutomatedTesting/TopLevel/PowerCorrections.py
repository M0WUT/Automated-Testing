import logging
from AutomatedTesting.TopLevel.UsefulFunctions import readable_freq


class PowerCorrections():
    def __init__(self, sigGen, powerMeter, freqRange, calibrationPower=-30):
        self.sigGen = sigGen
        self.powerMeter = powerMeter
        self.freqRange = freqRange
        self.calibrationPower = calibrationPower
        self.corrections = {}
        sigGen.set_freq(min(freqRange))
        sigGen.set_power(self.calibrationPower)

        logging.debug("Waiting for user intervention")

        input(
            "Please connect up system without DUT and press "
            "any key to normalise..."
        )
        logging.debug("User intervention complete")
        self.sigGen.enable_output()

        # Find power that produces >-35dB at power meter, just so this
        # doesn't take forever
        measuredPower = self.powerMeter.measure_power(min(freqRange))
        if(measuredPower < -35):
            self.calibrationPower += (self.calibrationPower - measuredPower)
            logging.info(
                f"Calibration power to low, "
                f"adjusting to {self.calibrationPower}"
            )
            self.sigGen.set_power(self.calibrationPower)
            assert self.powerMeter.measure_power(min(freqRange) > -35)

        for freq in self.freqRange:
            self.sigGen.set_freq(freq)
            measuredPower = self.powerMeter.measure_power()
            cableLoss = self.calibrationPower - measuredPower
            self.corrections[freq] = cableLoss

        self.sigGen.disable_output()
        logging.debug("Waiting for user intervention")

        input(
            "Please connect up system to DUT and press "
            "any key to continue..."
        )
        logging.debug("User intervention complete")

    def correctedPower(self, freq, power):
        if freq not in self.corrections.keys():
            logging.warning(
                f"Power correction requested at unmeasured freq: "
                f"{readable_freq(freq)}. Correction is approximated"
            )
            raise NotImplementedError
        else:
            return power + self.corrections[freq]
