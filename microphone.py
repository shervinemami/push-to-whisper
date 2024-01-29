# coding: utf-8

# Allow to efficiently record audio from the mic using pyaudio (wrapper for PortAudio).
# By Shervin Emami (shervin.emami@gmail.com), Jan 2024.

# If the default mic number isn't working for you, set your microphone PortAudio index here.
# You can find your mic numbers by running the Python code at "https://stackoverflow.com/a/39677871/199142"
MIC_DEVICE_INDEX = None

import sys
import pyaudio              # For audio from microphone
import wave                 # For saving to a wav file


CHUNK = 1024                # Record chunks of audio samples to improve efficiency
FORMAT = pyaudio.paInt16    # Use 16-bit audio (2 bytes per sample)
CHANNELS = 1                # We only use mono audio for speech rec
RATE = 44100                # 44.1kHz is the most common mic sampling rate


# RecordingFile class, based on https://gist.github.com/sloria/5693955
class RecordingFile(object):
    '''A recorder class for recording audio to a WAV file.
    Records in mono by default.
    Note that if you call start_recording() & stop_recording() multiple times, it will append onto the same wav file.
    '''

    def __init__(self, mode='wb'):
        self.mode = mode
        self.channels = CHANNELS
        self.rate = RATE
        self.frames_per_buffer = CHUNK
        # Initialise PyAudio (wrapper for PortAudio)
        self._pa = pyaudio.PyAudio()
        print()   # On some systems, initialising PortAudio causes a large amount of text messages to be displayed.
        self._stream = None

    def __enter__(self):
        return self

    def __exit__(self, exception, value, traceback):
        self.close()

    def record_for_fixed_duration(self, duration, fname):
        # Use a stream with no callback function in blocking mode
        self.wavefile = self._prepare_file(fname, self.mode)   # Moved from the __init__ function to support new filenames
        self._stream = self._pa.open(input_device_index=MIC_DEVICE_INDEX, format=pyaudio.paInt16,
                                        channels=self.channels, rate=self.rate,
                                        input=True, frames_per_buffer=self.frames_per_buffer)
        for _ in range(int(self.rate / self.frames_per_buffer * duration)):
            audio = self._stream.read(self.frames_per_buffer)
            self.wavefile.writeframes(audio)
        return None

    def start_recording(self, fname):
        # Use a stream with a callback in non-blocking mode
        self.wavefile = self._prepare_file(fname, self.mode)   # Moved from the __init__ function to support new filenames
        self._stream = self._pa.open(input_device_index=MIC_DEVICE_INDEX, format=pyaudio.paInt16,
                                        channels=self.channels, rate=self.rate,
                                        input=True, frames_per_buffer=self.frames_per_buffer,
                                        stream_callback=self.get_callback())
        self._stream.start_stream()
        return self

    def stop_recording(self):
        self._stream.stop_stream()
        return self

    def get_callback(self):
        # Wraps a pyaudio callback function where we save the latest data
        def callback(in_data, frame_count, time_info, status):
            self.wavefile.writeframes(in_data)
            return in_data, pyaudio.paContinue
        return callback

    def close(self):
        self._stream.close()
        self._pa.terminate()
        self.wavefile.close()

    def _prepare_file(self, fname, mode='wb'):
        wavefile = wave.open(fname, mode)
        if not wavefile:
            print("ERROR: Couldn't open output file '" + fname + "' for saving mic audio.")
            sys.exit(1)
        wavefile.setnchannels(self.channels)
        wavefile.setsampwidth(self._pa.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        return wavefile
