import os
import speech_recognition as sr
from gtts import gTTS
import csv
import subprocess

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
    print("\n[INFO] Recording from INMP441...\n")
    subprocess.run(
        ["arecord", "-D", "hw:2,0", "-f", "S32_LE", "-r", "48000", "-c", "2", "test.wav", "-d", "4"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    print("\n[INFO] Amplifying audio...\n")
    subprocess.run(
        ["ffmpeg", "-y", "-i", "test.wav", "-filter:a", "volume=14.0", "louder.wav"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

# Recognize text from WAV file
def get_audio_from_wav(file_path="./louder.wav"):
    print("\n[INFO] Recognizing audio...\n")
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
        print(f"\n[INFO] You said: {text}\n")
        return text.lower()
    except Exception as e:
        print(f"\n[ERROR] Could not understand audio: {str(e)}\n")
        return ""

# Match recognized text with phrases in the dictionary
def check_for_phrases_in_text(text, phrase_dict):
    english_phrases = list(phrase_dict.keys())
    hindi_phrases = [v['hindi'] for v in phrase_dict.values()]
    transliterations = [v['transliteration'] for v in phrase_dict.values()]

    text_words = text.lower().split()  # Simple split by space

    for word in text_words:
        if word in english_phrases:
            print(f"\n[INFO] Help keyword detected in English: {word}\n")
            return 1
        if word in hindi_phrases:
            print(f"\n[INFO] Help keyword detected in Hindi: {word}\n")
            return 1
        if word in transliterations:
            print(f"\n[INFO] Help keyword detected in Transliteration: {word}\n")
            return 1

    print("\n[WARN] No help keyword detected.\n")
    return 0

# Main loop
if __name__ == "__main__":
    csv_file_path = "./ML_Models/Help_Keyword_Detection/help_words_dataset.csv"
    phrases = load_phrases_from_csv(csv_file_path)

    while True:
        record_and_process_audio()
        recognized_text = get_audio_from_wav()
        check_for_phrases_in_text(recognized_text, phrases)
