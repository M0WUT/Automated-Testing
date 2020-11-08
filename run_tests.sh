#!/bin/bash
source .venv/bin/activate
pytest --cov-report term-missing --cov=AutomatedTesting unit-tests/ --cache-clear --flake8 AutomatedTesting
