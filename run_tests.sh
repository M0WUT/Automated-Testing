#!/bin/bash
source .venv/bin/activate
pytest --cache-clear --flake8 --cov-report term-missing --cov=AutomatedTesting unit-tests/