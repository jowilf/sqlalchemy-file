#!/usr/bin/env bash

set -e
set -x

coverage combine
coverage report --show-missing
coverage xml
