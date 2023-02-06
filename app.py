import io
import sys, os
import soundcard as sc
import soundfile as sf
import speech_recognition as sr
import time
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QDesktopWidget, QVBoxLayout, QWidget, QSizePolicy, QComboBox, QDialog, QFormLayout, QPushButton
from PyQt5.QtCore import QTimer, Qt, QSize, QThread, pyqtSignal
from googletrans import Translator


OUTPUT_FILE_NAME = "out.wav"     # file name.
SAMPLE_RATE = 48000              # [Hz]. sampling rate.
RECORD_SEC = 6                   # [sec]. duration recording audio.

language_codes = {
    "1": "en-US",
    "2": "fr-FR",
    "3": "de-DE",
    "4": "es-ES",
    "5": "it-IT",
    "6": "pt-br",
    "7": "pt-PT",
    "8": "ru-RU",
    "9": "zh-CN",
    "10": "hi-IN",
    "11": "ja-JP",
    "12": "ko",
    "13": "fil-PH",
    "14": "nl-NL",
    "15": "nl-NL"

}

target_lang = {
    "1": "en",
    "2": "es",
    "3": "fr",
    "4": "de",
    "5": "it",
    "6": "pt",
    "7": "ru",
    "8": "zh-CN",
    "9": "hi",
    "10": "ja",
    "11": "ko",
    "12": "fil",
    "13": "nl"
}

class LanguageSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select languages")

        # create form layout
        layout = QFormLayout()

        # create combo boxes
        self.source_combo = QComboBox()
        self.source_combo.addItems([f"{value}" for key, value in language_codes.items()])
        layout.addRow("Source language:", self.source_combo)

        self.target_combo = QComboBox()
        self.target_combo.addItems([f"{value}" for key, value in target_lang.items()])
        layout.addRow("Target language:", self.target_combo)

        self.record_sec = QComboBox()
        for i in range(5, 21):
            self.record_sec.addItem(str(i))
        layout.addRow("Recording seconds", self.record_sec)

        # create "Select" button
        select_button = QPushButton("Select")
        select_button.clicked.connect(self.accept)
        layout.addRow(select_button)

        self.setLayout(layout)
    def get_seconds(self):
        seconds = int(self.record_sec.currentText())
        return seconds
    def get_selected_languages(self):
        source_language = self.source_combo.currentText()
        target_language = self.target_combo.currentText()
        return source_language, target_language

class Read(QThread):
    stream_generated = pyqtSignal(io.BytesIO)
    def __init__(self, seconds,parent=None):
        super().__init__(parent)
        self.seconds = seconds

    def run(self):
        while True:
            with sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True).recorder(samplerate=SAMPLE_RATE) as mic:
                # record audio with loopback from default speaker.
                data = mic.record(numframes=SAMPLE_RATE * self.seconds)
                buffer = io.BytesIO()
                sf.write(buffer, data[:, 0], samplerate=SAMPLE_RATE,format='wav')
            self.stream_generated.emit(buffer)


class Process(QThread):
    result_ready = pyqtSignal(str)
    def __init__(self, selected,parent=None):
        super().__init__(parent)
        self.language, self.target = selected
        print(selected)

    def transcribe_audio(self, audio_stream):
        r = sr.Recognizer()
        with io.BytesIO(audio_stream) as f:
            audio_file = sr.AudioFile(f)
            with audio_file as source:
                audio_data = r.record(source)
        try:
            transcription = r.recognize_google(audio_data, language=self.language)
            print(f"Transcription: {transcription}")
            return transcription
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return None

    def translate_text(self, text):
        if text is None:
            return "Transcription Error"
        translator = Translator(service_urls=["translate.google.com"])
        translated_text = translator.translate(text, dest=self.target).text
        print(f"Translation: {translated_text}")
        return translated_text

    def runloop(self, stream):
        transcription = self.transcribe_audio(stream.getvalue())
        try:
            translation = self.translate_text(transcription)
        except Exception as e:
            retry_count = 0
            max_retries = 5
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
        self.result_ready.emit(translation)


class MainWindow(QMainWindow):
    def __init__(self, selected, seconds,parent=None):
        super().__init__(parent)

        #self.show_language_selector()
        self.label = QLabel("Waiting for translation...")
        self.label.setStyleSheet("font-size: 20pt;")  # adjust font size
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        desktop = QDesktopWidget()
        self.screen = desktop.screenGeometry(0)
        self.move(self.screen.left() + int((self.screen.width() - self.width()) / 2),
                  self.screen.top() + int((self.screen.height() - self.height()) / 2))

        self.Read_thread = Read(seconds)
        self.Process_thread = Process(selected)
        self.Read_thread.stream_generated.connect(self.Process_thread.runloop)
        self.Process_thread.result_ready.connect(self.update_label)

        self.Read_thread.start()

    def update_label(self, result):
        self.label.setText(str(result))
        max_width = int(self.screen.width() * 0.8)
        self.resize(min(self.label.sizeHint().width(), max_width) + 40, self.label.sizeHint().height() + 40)


app = QApplication(sys.argv)
selector = LanguageSelector()
if selector.exec_() == QDialog.Accepted:
    main_window = MainWindow(selector.get_selected_languages(),selector.get_seconds())
    #main_window.setAttribute(Qt.WA_TranslucentBackground, True)
    main_window.setWindowOpacity(0.5)
    main_window.show()
    sys.exit(app.exec_())
