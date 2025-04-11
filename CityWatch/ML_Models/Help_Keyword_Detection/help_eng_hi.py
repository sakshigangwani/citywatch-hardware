import os
import speech_recognition as sr
from gtts import gTTS
import csv

# Function to speak text out loud
def speak(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    filename = "voice.mp3"
    tts.save(filename)
   # os.system(f"start {filename}")  # Plays the saved file

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

# Function to get audio input and return recognized text
def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio)
            print("You said: ", said)
        except Exception as e:
            print("Sorry, could not understand the audio. Error: " + str(e))

    return said.lower()

# Function to match recognized text with phrases in the dictionary
def check_for_phrases_in_text(text, phrase_dict):
    text = text.strip().lower()  # Clean and standardize the recognized text
    
    print(f"Checking text: {text}")
    
    for english_phrase, phrases in phrase_dict.items():
        hindi_phrase = phrases['hindi']
        transliteration = phrases['transliteration']
        
        # Check if the recognized text matches the English phrase
        if text == english_phrase:
            print(f"Matched English phrase: {english_phrase}")
            speak(f"The translation is: {hindi_phrase}", lang="hi")
            return
        
        # Check if the recognized text matches the transliteration
        if transliteration and text == transliteration:
            print(f"Matched transliteration: {transliteration}")
            speak(f"The translation is: {hindi_phrase}", lang="hi")
            return
    
    print("No matching phrase found.")

# Main code logic
if __name__ == "__main__":
    # Load the phrases from CSV
    csv_file_path = "help_words_dataset.csv"  # Update with the correct path to your CSV file
    phrases = load_phrases_from_csv(csv_file_path)

    while True:
        # Get audio from microphone
        text = get_audio()

        # Check if the recognized text contains any key phrases
        check_for_phrases_in_text(text, phrases)
