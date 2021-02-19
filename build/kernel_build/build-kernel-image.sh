#!/bin/bash


tar cf kernel-4.19.125.tar lib/ boot/

echo "
Build Successfully

RUN:

    sudo docker import kernel-4.19.125.tar ztest:kernel-4.19.125
    
    sudo ignite kernel import ztest:kernel-4.19.125 --runtime docker

to add the kernel to ignite
"
