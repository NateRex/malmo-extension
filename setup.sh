#!/bin/bash

# ensure we are running from the script's directory
cd "$(dirname "$0")"

malmopath="${MALMO_PATH?MALMO_PATH has not been set.}"

cp $malmopath/Python_Examples/MalmoPython.so ./lib
cp $malmopath/Python_Examples/malmoutils.py ./lib