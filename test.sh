#!/bin/bash
PYTHONPATH=. py.test -v
PYTHONPATH=. pytest --durations=6 --cov-report=term-missing --cov=.
