#!/bin/bash

ping -q -c 1 db-gnuhealth || exit 1
wget -t 1 -T 5 -q --spider http://localhost:8000 || exit 1
