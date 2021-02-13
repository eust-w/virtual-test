#!/bin/bash

rm -rf dist/
python setup.py sdist
sudo pip install dist/ztest*
