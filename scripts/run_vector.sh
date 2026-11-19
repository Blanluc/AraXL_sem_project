#!/bin/bash
cd /scratch/socdaml_araxl/AraXL/apps
rm TSVC_2/src/*.o
make bin/tsvc
cd /scratch/socdaml_araxl/AraXL/hardware
make sim app=tsvc
#make simc app=tsvc