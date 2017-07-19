#!/bin/bash
py.test -v test_reican.py

pytest --durations=5 --cov-report=term-missing --cov=. test_reican.py
