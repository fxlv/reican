#!/bin/bash
py.test -v test_reican.py

pytest --cov-report=term-missing --cov=. test_reican.py