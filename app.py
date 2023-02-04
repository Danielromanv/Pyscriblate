import io
import sys, os
import soundcard as sc
import soundfile as sf
import speech_recognition as sr
import time
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QDesktopWidget
from PyQt5.QtCore import QTimer, Qt, QSize
from googletrans import Translator

class MainWindow(QMainWindow):
    def __init__(self, translation):
        super().__init__()
        self.translation = translation
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Translation")
        label = QLabel(self.translation, self)
        label.setStyleSheet("font-size: 20pt;")  # adjust font size
        label.setMargin(20)
        self.setCentralWidget(label)
        desktop = QDesktopWidget()
        screen = desktop.screenGeometry(1) if desktop.screenCount() > 1 else desktop.screenGeometry()
        size = self.geometry()
        self.move(screen.left() + int((screen.width()-size.width())/2), screen.top() + int((screen.height()-size.height())/2))
        self.resize(label.sizeHint() + QSize(40, 40))

OUTPUT_FILE_NAME = "out.wav"    # file name.
SAMPLE_RATE = 48000              # [Hz]. sampling rate.
RECORD_SEC = 15                  # [sec]. duration recording audio.
TARGET_LANGUAGE = "en"   # target language code

def transcribe_audio(audio_stream,language):
    r = sr.Recognizer()
    with io.BytesIO(audio_stream) as f:
        audio_file = sr.AudioFile(f)
        with audio_file as source:
            audio_data = r.record(source)
    try:
        transcription = r.recognize_google(audio_data, language=language)
        print(f"Transcription: {transcription}")
        return transcription
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def translate_text(text):
    if text is None:
        return None
    translator = Translator(service_urls=["translate.google.com"])
    translated_text = translator.translate(text, dest=TARGET_LANGUAGE).text
    print(f"Translation: {translated_text}")
    return translated_text

def run_translate_loop(language):
    app = QApplication([])
    while True:
        # Record audio from the output device
        with sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True).recorder(samplerate=SAMPLE_RATE) as mic:
            # record audio with loopback from default speaker.
            data = mic.record(numframes=SAMPLE_RATE * RECORD_SEC)
            buffer = io.BytesIO()
            sf.write(buffer, data[:, 0], samplerate=SAMPLE_RATE,format='wav')

        # Transcribe the recorded audio
        transcription = transcribe_audio(buffer.getvalue(),language)
        try:
            translation = translate_text(transcription)
        except Exception as e:
            retry_count = 0
            max_retries = 3
            while retry_count < max_retries:
                retry_count += 1
                print(f"Error translating audio, retrying... (attempt {retry_count} of {max_retries})")
                try:
                    translation = translate_text(transcription)
                    break
                except Exception as e:
                    if retry_count == max_retries:
                        print(f"Error transcribing audio: {e}")
                        translation = "Error al traducir"

language_codes = {
    "1": "en-US",
    "2": "fr-FR",
    "3": "de-DE",
    "4": "es-ES",
    "5": "it-IT",
    "6": "pt-PT",
    "7": "ru-RU",
    "8": "zh-CN",
    "9": "hi-IN",
    "10": "ja-JP",
    "11": "fil-PH",
    "12": "nl-NL"
}

print("Select Source language:")
print("1. English (en-US)")
print("2. French (fr-FR)")
print("3. German (de-DE)")
print("4. Spanish (es-ES)")
print("5. Italian (it-IT)")
print("6. Portuguese (pt-PT)")
print("7. Russian (ru-RU)")
print("8. Chinese (zh-CN)")
print("9. Hindi (hi-IN)")
print("10. Japanese (ja-JP)")
print("11. Tagalog (fil-PH)")
print("12. Dutch (nl-NL)")

user_input = input("Enter number: ")
language = language_codes.get(user_input)

target_lang = {
    "1": "en",
    "2": "es",
}
print("Select Target language:")
print("1. English (en-US)")
print("2. Spanish (es-ES)")

user_input = input("Enter number: ")
TARGET_LANGUAGE = target_lang.get(user_input)

if language:
    print(f"Selected language: {language}")
else:
    print("Invalid input")

run_translate_loop(language)
