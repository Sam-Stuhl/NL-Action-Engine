import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import AzureChatPromptExecutionSettings
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.weather_plugin import WeatherPlugin
from plugins.phillips_hue_lights_plugin import LightsPlugin

class SKManager:
    def __init__(self, plugins: list[dict]):
        self.plugins = plugins
        
        self.kernel = sk.Kernel()
        self.chat_completion = AzureChatCompletion()
        
        self.kernel.add_service(self.chat_completion)
        
        # Enable Planning
        self.execution_setting = AzureChatPromptExecutionSettings()
        self.execution_setting.function_choice_behavior = FunctionChoiceBehavior.Auto()
        
        self.history = ChatHistory()
        
        self.init_plugins()
    
    def init_plugins(self) -> None:
        try:
            for plugin in self.plugins:
                self.kernel.add_plugin(
                    plugin=plugin["plugin"],
                    plugin_name=plugin["plugin_name"]
                )
        except Exception as e:
            raise e
        
    async def make_user_request(self, user_message: str):
        self.history.add_user_message(user_message)

        result = await self.chat_completion.get_chat_message_content(
            chat_history=self.history,
            settings=self.execution_setting,
            kernel=self.kernel
        )
        
        self.history.add_assistant_message(str(result))
        
        return result
                
    async def start_simple_chat(self, is_logging_on: bool = False) -> None:
        if is_logging_on:
            logging.basicConfig(level=logging.DEBUG)
        
        while True:
            user_message = input("Type a request or say 'exit' to end the chat > ")
            if user_message.lower() == "exit":
                print("Exiting the chat. Goodbye!")
                break
            
            result = await self.make_user_request(user_message)
            
            print("Assistant > " + str(result))
            
            
if __name__ == "__main__":
    import asyncio
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
    
    async def main():
        await skm.start_simple_chat()
        
    asyncio.run(main())