#!/usr/bin/env python3
# coding: utf-8

# Simply list all detected audio input devices (microphone device IDs) for use with PyAudio / PortAudio.
# By Shervin Emami, 2024

import pyaudio
 
# Initialise PyAudio (wrapper for PortAudio)
audio = pyaudio.PyAudio()
print()   # On some systems, initialising PortAudio causes a large amount of text messages to be displayed.

print("---------------------- Audio Input Device List: ---------------------")
info = audio.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
for i in range(0, numdevices):
    print("Input Device", i, ": ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))

