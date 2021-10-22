#!/bin/bash
pytest --skipSigGen --cov-report term-missing --cov=AutomatedTesting unit-tests/ --cache-clear --flake8 AutomatedTesting
