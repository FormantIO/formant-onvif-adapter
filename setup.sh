#!/usr/bin/env bash
set -e

# Skip apt dependencies to avoid sudo

# # enable all Ubuntu packages:
# sudo apt-add-repository universe
# sudo apt-add-repository multiverse
# sudo apt-add-repository restricted

# sudo apt-get update

# # install python3 dependencies
# sudo apt-get -y install python3-pip

# install the formant python module
pip3 install setuptools
pip3 install wheel
pip3 install -r requirements.txt

touch setup.lock
