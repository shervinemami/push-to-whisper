#!/usr/bin/env python3
# coding: utf-8

# Push-to-talk, using keyboard hotkeys to only use OpenAI Whisper speech recognition when asked.
# It's usually doing nothing. Once the hotkey is pressed down, it starts recording audio.
# Once the hotkey is released, it triggers Whisper speech recognition on that recording in the background,
# to press keys on the keyboard of whatever was dictated, allowing to use Whisper for writing emails, etc.
# The triggering of Whisper occurs in the background so it's possible to create a new recording while Whisper
# is running. There is also a hotkey to cancel the current Whisper/keyboard task for when the user realises
# they made a mistake in what they said.
# By Shervin Emami (shervin.emami@gmail.com), Jan 2024.
#
# It requires pyaudio and pynput, installable such as "pip install pyaudio pynput".
# If you get this error message such as with pyaudio v0.11 in Ubuntu 22.04:
#       SystemError: PY_SSIZE_T_CLEAN macro must be defined for '#' formats
#   Then upgrade to a more recent PyAudio version, such as by running this on Ubuntu/Debian:
#       sudo apt install portaudio19-dev
#       pip install --upgrade PyAudio==0.2.12


# If the default mic number isn't working for you, set your microphone PortAudio index here.
# You can find your mic numbers by running the Python code at "https://stackoverflow.com/a/39677871/199142"
MIC_DEVICE_INDEX = None


# If you have a BlinkStick USB-controlled RGB LED, then set this to True.
ENABLE_BLINKSTICK = True

# Enable this for debugging, it will show every key that's caught.
SHOW_ALL_KEYS = False

import os
import sys
from pynput import keyboard     # To emulate typing keypresses

from microphone import RecordingFile
from blinkstick_LED import updateLED


# Keep the mic recording device open at all times, for faster starting & stopping    
rec_file = RecordingFile()
file_counter = 0


def startDictation():
    global rec_file
    global file_counter
    #os.system("/Core/Custom/switch_mic_to_talon_from_kaldi.sh")

    # Start recording the mic audio into our wav file
    wav_filename = "recording" + str(file_counter) + ".wav"
    print("Recording to '" + wav_filename + "'...")
    rec_file.start_recording(wav_filename)

def stopDictation():
    global rec_file
    global file_counter

    #os.system("/Core/Custom/switch_mic_to_kaldi_from_talon.sh")
    rec_file.stop_recording()
    file_counter = file_counter + 1
    print('Done')


# Hotkey listening functionality, taken from my "_dictation_mode.py" file.
# A blocking function that can be used as a thread function callback if desired.
def setupHotkeysForBackends_blocking(arg):

    print("Waiting for global hotkeys that switch recognition backends ...")

    # This function is unused because we use on_press & on_release directly. But it's left here for compilation purposes
    def on_activate():
        print('Global hotkey activated!')

    def key_pressed(a):
        if SHOW_ALL_KEYS:
            print('key pressed!', a)
        # If the user is holding down the NumLock (Num Lock) key, switch to Dictation mode.
        if a == keyboard.Key.num_lock:
            updateLED("on", "Normal")
            print('Global dictation-mode hotkey pressed!', a)
            startDictation()
            print('Handled.')

    def key_released(a):
        if SHOW_ALL_KEYS:
            print('key released!', a)
        # If the user released the NumLock (Num Lock) key, switch back to Command mode.
        if a == keyboard.Key.num_lock:
            updateLED("on", "Command")
            print('Global dictation-mode hotkey released!', a)
            stopDictation()
            print('Handled.')

        #elif a == keyboard.Key.num_lock:
        #    print('Global hotkey released!', a)
        #    self.grammar.status = 2
        #elif a == keyboard.Key.f13:
        #    print('Global hotkey released!', a)
        #elif a == keyboard.Key.f14:
        #    print('Global hotkey released!', a)
        #elif a == keyboard.Key.f15:
        #    print('Global hotkey released!', a)
        #elif a == keyboard.Key.f16:
        #    print('Global hotkey released!', a)
        #elif a == keyboard.Key.ctrl_r:
        #    print('Global hotkey released!', a)
        #elif a == keyboard.Key.cmd_r:
        #    print('Global hotkey released!', a)
        #else:
        #    print('UNKNOWN key released.', a)

    with keyboard.Listener(
            on_press=key_pressed,
            on_release=key_released) as h:
        h.join()


def main(args):
    print("Push-to-talk for dictating with OpenAI Whisper speech recognition. By Shervin Emami 2024.")
    print("Started listening for keyboard hotkeys.")

    # Allow switching recognition backends
    setupHotkeysForBackends_blocking(0,)    # Blocking

    # Should never reach here!
    #pa.terminate()  # Close PyAudio
    print("Finished listening for keyboard hotkeys.")


if __name__ == "__main__":
    main(sys.argv[1:])
