#!/usr/bin/env python3
# coding: utf-8

print("Push-to-talk for dictating with OpenAI Whisper speech recognition. By Shervin Emami 2024.\n")

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


# Whisper speech recognition settings
model_filename = "medium.en"    # Can be "tiny", "small", "medium", "large-v3"
COMPUTE_DEVICE = "cuda"         # Can be "cuda" (NVIDIA GPU) or "cpu" (any other scenario)
#COMPUTE_DEVICE = "cpu"         # Can be "cuda" (NVIDIA GPU) or "cpu" (any other scenario)
COMPUTE_TYPE = "int8_float16"   # Can be "float32", "float16", "int16", "int8_float16", "int8", and possibly "bfloat16"
#COMPUTE_TYPE = "int8"           # Can be "float32", "float16", "int16", "int8_float16", "int8", and possibly "bfloat16"
LANGUAGE = "en"                 # Set to the Whisper language name. eg: "en" for English, "fr" for French
BEAM_SIZE = 5                   # Note: Faster-Whisper requires beam_size to be atleast 1, while OpenAI Whisper can take "None"
BEST_OF = 5
TEMPERATURE = 0.3
PATIENCE = 1.0                  # Must be larger than 0

# Set to True if you want it to try using faster-whisper instead of OpenAI whisper.
USE_FASTER_WHISPER = True
# Defaults to using 1 CPU worker threads, but can use more, at the expense of more RAM usage.
NUM_FASTER_WHISPER_WORKERS=1

# Whisper allows passing "prompt" that is intended to be the previous sentence or some similar related text, to give a hint 
# about what it should expect. This includes formatting, so for example giving a hint of "40's" can push whisper closer to
# decoding the phrase "forties" as "40's" instead of "40s".
# When dictating long passages for many minutes, it's normal to set up the prompt to be the previous output
# from Whisper. But this increases how often Whisper hallucinates, which unfortunately happens often. For computer
# control, it's more common that each spoken sentence will have almost no relavence to previous spoken sentences, so
# here we will use a fixed prompt string, formatted in the way that we like.
HINT_PROMPT = "oh OK yeah sure, in my 40's I mostly benchmarked a profile of ARM CPU core optimisations such as on A53 CPU's"


# If you have a BlinkStick USB-controlled RGB LED, then set this to True.
ENABLE_BLINKSTICK = True

# Enable this for debugging the hotkey, it will show every key that's caught.
SHOW_ALL_KEYS = False

# When this is True, it will type the resulting text on your keyboard. Set to False if you only want to see the results in the console.
ENABLE_TYPING = True



import os
import sys
import time
import atexit

from pynput import keyboard     # To wait for hotkeys, and to emulate typing keypresses

from microphone import RecordingFile


# Load the OpenAI Whisper model
print("Please wait while we load Whisper model '" + model_filename + "' during startup, this can take a long time ...")
model = None
# Load either Faster-Whisper or OpenAI Whisper
if USE_FASTER_WHISPER:
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_filename, device=COMPUTE_DEVICE, compute_type=COMPUTE_TYPE, num_workers=NUM_FASTER_WHISPER_WORKERS)
        # or run on CPU with INT8
        # model = WhisperModel(model_filename, device="cpu", compute_type="int8", num_workers=num_workers)
        USE_FASTER_WHISPER = True    # Only set the flag if we succesfully imported the library and opened the model.
    except ImportError:
        print("ERROR: faster_whisper not installed or not working, falling back to OpenAI whisper")
if not USE_FASTER_WHISPER:
    import whisper
    model = whisper.load_model(model_filename)


# Possibly show our mode on a BlinkStick USB LED, if enabled and available.
if ENABLE_BLINKSTICK:
    try:
        from blinkstick_LED import updateLED
    except:
        ENABLE_BLINKSTICK = False
if not ENABLE_BLINKSTICK:
    def updateLED(mode):
        pass


# Clean up a sentence. If index > 0, also place a fullstop at the begining.
def postprocessSentence(text, index):
    sentence = text
    # Remove initial whitespace
    if sentence.startswith(" "):
        sentence = sentence[1:]
    # Capitalise the sentence
    sentence = sentence[0].upper() + sentence[1:]
    if index > 0:
        # Begin the sentence with a fullstop and a space
        sentence = ". " + sentence
    # Remove trailing "..." that Whisper sometimes includes at the end
    if sentence.endswith("..."):
        sentence = sentence[:-2]
    return sentence


# Perform speech recognition on the saved wav file
def performSpeechRecOnFile(wav_filename):
    # Decode the audio
    result = ""
    if not USE_FASTER_WHISPER:
        audio = whisper.load_audio(wav_filename)

        # Pad/trim it to fit 30 seconds just like the training set.
        audio = whisper.pad_or_trim(audio)

        start_inference = time.perf_counter()

        # Make log-mel spectrogram and move it to the same device as the model (GPU)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)

        # Decode using OpenAI Whisper.
        # Note that as of January 2024, OpenAI Whisper isn't optimised for FP16, so it's better to use FP32 mode.
        options = whisper.DecodingOptions(language=LANGUAGE, fp16=False, prompt=HINT_PROMPT, best_of=BEST_OF,
                                          beam_size=BEAM_SIZE, temperature=TEMPERATURE, patience=PATIENCE)
        # Perform the transcription now.
        decoder_result = whisper.decode(model, mel, options)
        elapsed_inference = time.perf_counter() - start_inference

        # Print the recognition result
        print("  --> ", decoder_result.text)
        # Clean up the sentence.
        result = postprocessSentence(decoder_result.text, 0)

    else:
        start_inference = time.perf_counter()
        # We don't need a VAD algorithm since we are manually using a hotkey for start & stop of our audio.
        vad_filter = False
        # Note that Faster-Whisper returns a generator and doesn't actually perform the transcription
        # until you use the 'segments' variable!
        # For more info about the options, see "https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py"
        segments, info = model.transcribe(wav_filename, language=LANGUAGE, initial_prompt=HINT_PROMPT,
                                          condition_on_previous_text=False, best_of=BEST_OF, beam_size=BEAM_SIZE, temperature=TEMPERATURE, patience=PATIENCE, word_timestamps=False, vad_filter=vad_filter)
        # Perform the transcription now.
        segments = list(segments)
        elapsed_inference = time.perf_counter() - start_inference

        # Print the recognition result.
        # Faster-whisper returns the results as potentially multiple segments, where each segment might be a full sentence.
        for segment in segments:
            print("  --> ", segment.text)

        # Convert the multiple sentences into a single output string.

        n = len(segments)
        if n > 0:
            # Clean up a sentence. If index > 0, also place a fullstop at the begining.
            result = postprocessSentence(segments[0].text, 0)

        # If there are multiple sentences, perform some post-processing to merge the sentences.
        i = 1  # Loop but skip the first sentence
        while i < n:
            sentence = postprocessSentence(segments[i].text, i)
            # Combine the modified sentences
            result = result + sentence
            i = i+1


    print("[Inference clock time:", '{0:.3f}'.format(elapsed_inference), "seconds]")
    return result


def typeOnKeyboard(phrase):
    keyb = keyboard.Controller()
    for character in phrase:
        try:
            keyb.type(character)
            time.sleep(0.0025)
        except:
            print("Empty or unknown symbol", character)
            continue


# Keep the mic recording device open at all times, for faster starting & stopping    
rec_file = RecordingFile()
file_counter = 0
wav_filename = ""
recognitions_in_progress = 0    # A counter of how many recognitions are currently in progress. Should usually be 0 or 1.


def startDictation():
    global rec_file
    global file_counter
    global wav_filename
    global recognitions_in_progress

    # Mute the mic for my other speech recognition system, since we want to handle the mic instead.
    #try:
    #    os.system("/Core/Custom/mute_kaldi.sh")
    #except:
    #    pass

    if recognitions_in_progress > 0:
        print("User is trying to record something while recognition is still running. We'll move to a separate audio file.")

    # Start recording the mic audio into our wav file
    wav_filename = "recording" + str(recognitions_in_progress) + ".wav"
    print("Recording to '" + wav_filename + "'...")
    rec_file.start_recording(wav_filename)

def stopDictation():
    global rec_file
    global file_counter
    global wav_filename
    global recognitions_in_progress

    recognitions_in_progress = recognitions_in_progress + 1
    # Keep a local copy of the value for this iteration. If the user runs dictation during recognition, the global value will change.
    this_wav_filename = wav_filename

    # Save the file
    duration = rec_file.stop_recording()
    #file_counter = file_counter + 1   # Do we want to record into a new file each time?
    print("Saved", '{0:.3f}'.format(duration), "seconds into '" + this_wav_filename + "'.")

    # Unmute the mic for my other speech recognition system, since we are done for now.
    #try:
    #    os.system("/Core/Custom/unmute_kaldi.sh")
    #except:
    #    pass

    # Perform speech recognition on the saved wav file
    result = performSpeechRecOnFile(this_wav_filename)

    # Ensure we had enough time to say a word
    if duration < 0.45:
        result = ""

    # Check if we have a lot of generated text from a very short audio recording, since this usually means Whisper
    # has been hallucinating. Also check if the number of characters per second is very high.
    chars_per_second = len(result) / duration
    if (chars_per_second > 25 and len(result) > 40):
        result = ""
        print("Detected hallucination!")
        updateLED("Orange")    # Show the LED as Orange to signify a hallucination

    if ENABLE_TYPING:
        typeOnKeyboard(result)

    recognitions_in_progress = recognitions_in_progress - 1    



# Hotkey listening functionality, taken from my "_dictation_mode.py" file.
# A blocking function that can be used as a thread function callback if desired.
def setupHotkeysForBackends_blocking(arg):
    print("You can now start pressing the hotkeys!")

    # This function is unused because we use on_press & on_release directly. But it's left here for compilation purposes
    def on_activate():
        print('Global hotkey activated')

    def key_pressed(a):
        if SHOW_ALL_KEYS:
            print('key pressed:', a)
        # If the user is holding down the NumLock (Num Lock) key, switch to Dictation mode.
        if a == keyboard.Key.num_lock:
            updateLED("Normal")
            print()
            print('Global dictation-mode hotkey pressed:', a)
            startDictation()

    def key_released(a):
        if SHOW_ALL_KEYS:
            print('key released!', a)
        # If the user released the NumLock (Num Lock) key, switch back to Command mode.
        if a == keyboard.Key.num_lock:
            updateLED("Command")
            print('Global dictation-mode hotkey released:', a)
            stopDictation()

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
    # Call our onExit function before closing, since we usually run forever.
    atexit.register(onExit)

    # Since the first invocation of Whisper is significantly slower than others,
    # let's transcribe some initial data just to warm up Whisper.
    print("Initialising OpenAI Whisper ...")
    performSpeechRecOnFile("ready.wav")
    updateLED("Yellow")

    # Allow switching recognition backends
    setupHotkeysForBackends_blocking(0,)    # Blocking

    # Should never reach here!

def onExit():
    #pa.terminate()  # Close PyAudio
    print("Finished listening for keyboard hotkeys.")
    updateLED("off")


if __name__ == "__main__":
    main(sys.argv[1:])
