#!/usr/bin/env bash

set -e
set -x
ruff sqlalchemy_file tests docs_src --fix
black .
