#!/usr/bin/env bash

set -e
set -x

mypy sqlalchemy_file
flake8 sqlalchemy_file tests docs_src
black sqlalchemy_file tests docs_src --check
isort sqlalchemy_file tests docs_src --check-only