#!/usr/bin/bash

eval "$(conda shell.bash hook)"
conda activate pdf
python architecture_wikipedia_scraper.py
