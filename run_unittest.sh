#!/bin/bash

VENV_DIR_BIN=venv/bin/
SRC_DIR=src/

. $VENV_DIR_BIN/activate

export PYTHONPATH=$PYTHONPATH:$SRC_DIR

pytest $@ -s
deactivate
