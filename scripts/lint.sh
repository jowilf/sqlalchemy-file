#!/usr/bin/env bash

set -e
set -x

mypy sqlalchemy_file
ruff sqlalchemy_file tests
black sqlalchemy_file tests --check