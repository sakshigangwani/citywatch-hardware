import pyaudio
import numpy as np
import wave
import datetime
import os

##############################################
# function for setting up pyaudio
##############################################
def pyserial_start():
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio_format,
        rate=samp_rate,
        channels=chans,
        input_device_index=dev_index,
        input=True,
        frames_per_buffer=CHUNK
    )
    stream.stop_stream()
    return stream, audio

def pyserial_end():
    stream.close()
    audio.terminate()

##############################################
# function for grabbing data from buffer
##############################################
def data_grabber(rec_len):
    stream.start_stream()
    stream.read(CHUNK, exception_on_overflow=False)  # flush port first 
    print('Recording Started.')
    data_frames = []
    for _ in range(0, int((samp_rate * rec_len) / CHUNK)):
        stream_data = stream.read(CHUNK, exception_on_overflow=False)
        data_frames.append(stream_data)
    stream.stop_stream()
    print('Recording Stopped.')
    return data_frames

##############################################
# Save data as .wav file
##############################################
def data_saver(data_frames, t_0):
    data_folder = './data/'
    if not os.path.isdir(data_folder):
        os.mkdir(data_folder)
    filename = datetime.datetime.strftime(t_0, '%Y_%m_%d_%H_%M_%S_audio')
    wf = wave.open(data_folder + filename + '.wav', 'wb')
    wf.setnchannels(chans)
    wf.setsampwidth(audio.get_sample_size(pyaudio_format))
    wf.setframerate(samp_rate)
    wf.writeframes(b''.join(data_frames))
    wf.close()
    return filename

##############################################
# Main Data Acquisition Procedure
##############################################
if __name__ == "__main__":
    CHUNK = 44100  # frames to keep in buffer between reads
    samp_rate = 44100  # sample rate [Hz]
    pyaudio_format = pyaudio.paInt16  # 16-bit device
    chans = 1  # only read 1 channel
    dev_index = 0  # index of sound device

    stream, audio = pyserial_start()
    record_length = 5  # seconds to record

    input('Press Enter to Start Recording: ')
    data_frames = data_grabber(record_length)
    t_0 = datetime.datetime.now()
    data_saver(data_frames, t_0)

    pyserial_end()
