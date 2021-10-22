#!/bin/bash
pytest --skipSmb100a --skipPSU --cov-report term-missing --cov=AutomatedTesting unit-tests/ --cache-clear --flake8 AutomatedTesting
