import pyaudio

audio = pyaudio.PyAudio()

for ii in range(0, audio.get_device_count()):
    print(audio.get_device_info_by_index(ii))