import os
import speech_recognition as sr
from gtts import gTTS
import csv
import subprocess

# Function to speak text out loud
def speak(text, lang="hi"):
    tts = gTTS(text=text, lang=lang)
    filename = "./voice.mp3"
    tts.save(filename)
    os.system(f"mpg123 {filename}")  # Use mpg123 to play the file

# Function to clean the Hindi phrase and extract transliterations
def clean_hindi_phrase(hindi_phrase):
    if '(' in hindi_phrase:
        hindi_phrase, transliteration = hindi_phrase.split('(')
        transliteration = transliteration.replace(')', '').strip()
        return hindi_phrase.strip(), transliteration.strip()
    return hindi_phrase.strip(), None

# Load the CSV file into a dictionary
def load_phrases_from_csv(file_path):
    phrase_dict = {}
    with open(file_path, mode='r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip the header
        for row in csv_reader:
            english_phrase = row[0].strip().lower()
            hindi_phrase, transliteration = clean_hindi_phrase(row[1].strip().lower())
            phrase_dict[english_phrase] = {'hindi': hindi_phrase, 'transliteration': transliteration}
    return phrase_dict

# Record audio from INMP441 using arecord and amplify using ffmpeg
def record_and_process_audio():
    print("Recording from INMP441...")
    subprocess.run(["arecord", "-D", "hw:2,0", "-f", "S32_LE", "-r", "48000", "-c", "2", "test.wav", "-d", "4"], check=True)

    print("Amplifying audio...")
    subprocess.run(["ffmpeg", "-y", "-i", "test.wav", "-filter:a", "volume=14.0", "louder.wav"], check=True)

# Recognize text from WAV file
def get_audio_from_wav(file_path="./louder.wav"):
    print("Recognizing audio...")
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
        print("You said:", text)
        return text.lower()
    except Exception as e:
        print("Could not understand audio:", str(e))
        return ""

# Match recognized text with phrases in the dictionary
def check_for_phrases_in_text(text, phrase_dict):
    english_phrases = list(phrase_dict.keys())
    hindi_phrases = [v['hindi'] for v in phrase_dict.values()]
    transliterations = [v['transliteration'] for v in phrase_dict.values()]

    text_words = text.lower().split()  # Simple split by space

    for word in text_words:
        if word in english_phrases:
            print(f"Help keyword detected in English: {word}")
            # speak("Help keyword detected in English.")
            return
        if word in hindi_phrases:
            print(f"Help keyword detected in Hindi: {word}")
            # speak("Help keyword detected in Hindi.")
            return
        if word in transliterations:
            print(f"Help keyword detected in Transliteration: {word}")
            # speak("Help keyword detected in Transliteration.")
            return

    print("No help keyword detected.")

# Main loop
if __name__ == "__main__":
    csv_file_path = "./ML_Models/Help_Keyword_Detection/help_words_dataset.csv"
    phrases = load_phrases_from_csv(csv_file_path)

    while True:
        record_and_process_audio()
        recognized_text = get_audio_from_wav()
        check_for_phrases_in_text(recognized_text, phrases)
