#!/bin/bash

# Install dependencies (in caso non vengano installate dal build command)
pip install -r requirements.txt

# Avvia il bot
python bot.py
