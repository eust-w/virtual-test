#!/bin/bash

PKG_DIR=ztest-all
TARGET=ztest-all.tar.gz

rm -rf dist/
rm -rf $PKG_DIR
python setup.py sdist

mkdir $PKG_DIR
cp dist/ztest*.tar.gz $PKG_DIR
cp -r build/docker_build $PKG_DIR

cd build/kernel_build > /dev/null
bash build-kernel-image.sh > /dev/null
cd - > /dev/null

cp build/kernel_build/kernel-*.tar $PKG_DIR

tar czf $TARGET $PKG_DIR
rm -rf $PKG_DIR

echo "
Build Successfully: $TARGET
"

