class BaseTest():
    def generate_measurement_points(self):
        raise NotImplementedError

    def retrieve_results(self, results):
        for x in self.measurements:
            for y in results.measurements:
                if(y == x):
                    # This looks odd but the equality
                    # operator only checks the primary
                    # key so this copies the results
                    # into x
                    x.drainCurrent = y.drainCurrent
                    x.outputPower = y.outputPower
                    break
