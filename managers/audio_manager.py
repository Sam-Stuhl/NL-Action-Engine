from pyaudio import paInt16, PyAudio
import keyboard
import time
import wave

import openwakeword
from openwakeword.model import Model
import collections
import numpy as np
from datetime import datetime
import tempfile
import os
import whisper

class AudioManager:
    FORMAT = paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1280
    
    def __init__(
        self,
        wakeword_model_path: str, 
        whisper_model_name: str,
        enable_noise_suppression: bool = False,
        vad_threshold: float = 0.5, 
        inference_framework: str = "onnx",
    ):
        self.audio = PyAudio()
        self.stream = self.audio.open(
            format=AudioManager.FORMAT,
            channels=AudioManager.CHANNELS,
            rate=AudioManager.RATE,
            input=True,
            frames_per_buffer=AudioManager.CHUNK
        )
        
        
        self.vad_threshold = vad_threshold
        # Init openwakeword model
        self.owwModel = Model(
            wakeword_models=[wakeword_model_path],
            enable_speex_noise_suppression=enable_noise_suppression,
            vad_threshold=self.vad_threshold,
            inference_framework=inference_framework
        )
        
        # Init whisper model
        self.whisper_model = whisper.load_model(whisper_model_name)
        
    def start_audio_chat(self):
        last_save = time.time()
        activation_times = collections.defaultdict(list)
        
        print("Listening...")
        while True:
            mic_audio = np.frombuffer(self.stream.read(AudioManager.CHUNK, exception_on_overflow=False), dtype=np.int16)
            
            (detected_wake_word, last_save, activation_times) = self.detect_wake_word(mic_audio, last_save, activation_times)
            # print((detected_wake_word, last_save, activation_times))
            if detected_wake_word:
                print("Heard wake word.")
                print("Recording audio...")
                
                frames = self.record_audio()
                tmp = self.save_temp_wav_file(frames)
                
                print("Recorded request.")
                print("Transcribing...")
                
                result = whisper.transcribe(self.whisper_model, tmp, fp16=False)
                os.remove(tmp)
                
                print("Here's your transcript:\n  "  + result['text'])
                
                
                
                
        
    def detect_wake_word(self, mic_audio, last_save, activation_times) -> tuple[bool, float, collections.defaultdict]:    
        cooldown = 4
        save_delay = 1
            
        # Feed to openWakeWord model
        prediction = self.owwModel.predict(mic_audio)
        
        # Check for model activation
        for mdl in prediction.keys():
            if prediction[mdl] >= self.vad_threshold:
                activation_times[mdl].append(time.time())
            
            if activation_times.get(mdl) and (time.time() - last_save) >= cooldown and (time.time() - activation_times.get(mdl)[0]) >= save_delay:
                last_save = time.time()
                activation_times[mdl] = []
                #detect_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                return (True, last_save, activation_times)
        
        return (False, last_save, activation_times)
               
        
    def record_audio(self) -> list:
        frames = []
        
        silence_threshold = 500
        silence_duration = 1.5
        silent_chunks = 0
        max_silent = int(silence_duration * AudioManager.RATE / AudioManager.CHUNK)
        started = False
        
        while True:
            data = self.stream.read(AudioManager.CHUNK, exception_on_overflow=False)
            audio_chunk = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_chunk).mean()
            
            if volume > silence_threshold:
                started = True
                silent_chunks = 0
                frames.append(data)
            elif started:
                silent_chunks += 1
                frames.append(data)
                if silent_chunks >= max_silent:
                    break
            elif keyboard.is_pressed('space'):
                break
        return frames
        
    
    def simple_audio_record(self):
        frames = []
        print("Press SPACE to start recording.")
        keyboard.wait('space')
        print("Recording... Press SPACE to stop.")
        time.sleep(0.2)
        
        while True:
            try:
                data = self.stream.read(AudioManager.CHUNK, exception_on_overflow=False)
                frames.append(data)
            except KeyboardInterrupt:
                break
            if keyboard.is_pressed('space'):
                print("Stopping recording after a brief delay...")
                time.sleep(0.2)
                break
        self.stop()
        
        self.frames_to_wav(frames)
        
    def frames_to_wav(self, frames: list, output_filename) -> None:
        waveFile = wave.open(output_filename, 'wb')
        waveFile.setnchannels(AudioManager.CHANNELS)
        waveFile.setsampwidth(self.audio.get_sample_size(AudioManager.FORMAT))
        waveFile.setframerate(AudioManager.RATE)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()
    
    def save_temp_wav_file(self, frames: list) -> str:
        tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        tmp.close()
        self.frames_to_wav(frames, tmp.name)
        return tmp.name
            
    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
            
if __name__ == "__main__":
    jarvis_model_path = "/Users/sam/Library/CloudStorage/OneDrive-TimothyChristianSchool/Stem Internship/Microsoft/NL Action Engine/.venv/lib/python3.13/site-packages/openwakeword/resources/models/hey_jarvis_v0.1.onnx"
    whisper_model_name = 'tiny'
    am = AudioManager(jarvis_model_path, whisper_model_name)
    
    # am.simple_audio_record()
    
        
    # am.detect_wake_word(jarvis_model_path)
    am.start_audio_chat()
    am.stop()