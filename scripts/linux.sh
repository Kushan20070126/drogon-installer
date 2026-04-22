#!/bin/bash

set -e

sudo apt update
sudo apt install -y git cmake g++ libssl-dev uuid-dev

git clone https://github.com/drogonframework/drogon.git
cd drogon
git submodule update --init
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install