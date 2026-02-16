from managers.sk_manager import SKManager
from managers.audio_manager import AudioManager
from plugins.phillips_hue_lights_plugin import LightsPlugin
from plugins.weather_plugin import WeatherPlugin

import time
import collections
import numpy as np

async def main(sk_manager: SKManager, audio_manager: AudioManager):
    last_save = time.time()
    activation_times = collections.defaultdict(list)
    
    # Start conversation
    print("Say 'Hey Jarvis' followed by a request. Say 'Hey Jarvis, exit' to end the conversation.")
    
    while True:
        mic_audio = np.frombuffer(audio_manager.stream.read(AudioManager.CHUNK, exception_on_overflow=False), dtype=np.int16)
        (detected_wake_word, last_save, activation_times) = audio_manager.detect_wake_word(mic_audio, last_save, activation_times)
        
        if detected_wake_word:
            print("\033[1;32m* Listening...\033[0m")
            user_message = audio_manager.get_audio_after_wake_word()
            
            if user_message.lower() == 'exit':
                print("Exiting the chat. Goodbye!")
                break
            
            print("You > " + user_message)
            
            result = await sk_manager.make_user_request(user_message)
            
            print("Assistant > " + str(result))
            
            audio_manager.tts_response(str(result))
                
            
        
        
if __name__ == "__main__":
    lights = [
        {"id": "a60e6289-7979-4036-b1d5-a3795efba4b3", "name": "bedroom-light-1", "is_on": True, "brightness": 100.0, "color": {"x": 0.3865, "y":0.3784}},
        {"id": "7ac12c9c-4bc3-4792-83e2-67e93fa9ea6f", "name": "bedroom-light-2", "is_on": True, "brightness": 100.0, "color": {"x": 0.3865, "y":0.3784}},
        {"id": "4e8a1e19-63a6-49dd-bc8d-4dbb703e1652", "name": "bedroom-light-3", "is_on": True, "brightness": 100.0, "color": {"x": 0.3865, "y":0.3784}}
    ]
    groups = [
        {"id": "bac841b0-3881-4c55-ad41-15b3afa249aa", "name": "Sam's Bedroom", "is_on": True, "brightness": 100.0, "color": {"x": 0.3865, "y":0.3784}}
    ]

    plugins = [
        {"plugin": LightsPlugin(lights, groups), "plugin_name": "Lights"},
        {"plugin": WeatherPlugin(), "plugin_name": "Weather"}
    ]

    skm = SKManager(plugins)
    
    jarvis_model_path = "/Users/sam/Library/CloudStorage/OneDrive-TimothyChristianSchool/Stem Internship/Microsoft/NL Action Engine/.venv/lib/python3.13/site-packages/openwakeword/resources/models/hey_jarvis_v0.1.onnx"
    whisper_model_name = 'tiny'
    am = AudioManager(jarvis_model_path, whisper_model_name)
    
    import asyncio
    asyncio.run(main(skm, am))  
    