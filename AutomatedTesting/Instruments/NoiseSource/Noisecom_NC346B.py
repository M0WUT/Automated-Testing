from AutomatedTesting.Instruments.NoiseSource.NoiseSource import NoiseSource


class Noisecom_NC346(NoiseSource):
    def __init__(self):
        super().__init__(
            onVoltage=28,
            onCurrent=0.015,
            enr={
                10e6: 15.51,
                100e6: 15.43,
                1e9: 15.20,
                2e9: 15.09,
                3e9: 14.88,
                4e9: 14.75,
                5e9: 14.79,
                6e9: 14.72,
                7e9: 14.76,
                8e9: 14.87,
                9e9: 15.11,
                10e9: 15.35,
                11e9: 15.51,
                12e9: 15.63,
                13e9: 15.66,
                14e9: 15.59,
                16e9: 15.30,
                17e9: 15.06,
                18e9: 14.70,
            },
            name="Noisecom NC346B",
        )


if __name__ == "__main__":
    x = Noisecom_NC346()
