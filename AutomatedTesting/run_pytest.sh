#!/bin/bash
# run from top level of Git checkout
python -m pytest --full-trace --cov-report term-missing --cov=AutomatedTesting/Instruments AutomatedTesting/pytest/ --cache-clear