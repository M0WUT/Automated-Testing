#!/bin/bash
pytest --skipSmb100a --skipSdg2122x --cov-report term-missing --cov=. unit-tests/ --cache-clear #--flake8 .