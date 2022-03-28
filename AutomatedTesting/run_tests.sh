#!/bin/bash
pytest --skipSmb100a --skipSdg2122x --skipPSU --full-trace --cov-report term-missing --cov=. unit-tests/ --cache-clear #--flake8 .