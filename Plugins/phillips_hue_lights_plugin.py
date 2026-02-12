from typing import TypedDict, Annotated, List, Optional
from semantic_kernel.functions import kernel_function
from httpx import AsyncClient, HTTPError

import os
from dotenv import load_dotenv

load_dotenv()

class LightModel(TypedDict):
    id: str
    name: str
    is_on: bool
    brightness: float
    color: dict[str: float, str: float]
    
class GroupModel(TypedDict):
    id: str
    name: str
    is_on: bool
    brightness: float
    color: dict[str: float, str: float]

class LightsPlugin:
    # Constants
    BRIDGE_IP = os.getenv("PHILLIPS_HUE_BRIDGE_IP")
    APP_KEY = os.getenv("PHILLIPS_HUE_APP_KEY")
    BASE_URL = f"https://{BRIDGE_IP}/clip/v2/resource"
    HEADERS = {
        "hue-application-key": APP_KEY
    }
    
    def __init__(self, lights: list[LightModel], groups: list[GroupModel]):
        self.lights = lights
        self.groups = groups
    
    # --- Kernel Functions ---
    
    @kernel_function
    async def get_lights(self) -> List[LightModel]:
        """Gets a list of lights and their current state."""
        return self.lights
    
    @kernel_function
    async def get_light_state(self, id: Annotated[str, "The Id of the light"]) -> Optional[LightModel]:
        """Gets the state of a particular light."""
        for light in self.lights:
            if id == light["id"]:
                return light
        return None
    
    @kernel_function
    async def change_light_state(self, id: Annotated[str, "The Id of the light"], new_light_state: LightModel) -> Optional[LightModel | HTTPError]:
        """Changes the state of an individual light."""
        for light in self.lights:
            if light["id"] == id:
                light["is_on"] = new_light_state.get("is_on", light["is_on"])
                light["brightness"] = new_light_state.get("brightness", light["brightness"])
                light["color"] = new_light_state.get("color", light["color"])
                
                return await self._change_light(light)
        return None
    
    @kernel_function
    async def change_group_state(self, id: Annotated[str, "The Id of the group"], new_group_state: GroupModel) -> Optional[GroupModel | HTTPError]:
        """Changes the state of an individual light."""
        for group in self.groups:
            if group["id"] == id:
                group["is_on"] = new_group_state.get("is_on", group["is_on"])
                group["brightness"] = new_group_state.get("brightness", group["brightness"])
                group["color"] = new_group_state.get("color", group["color"])
                
                return await self._change_group(group)
        return None
    
    
    # --- Helper Functions ---
    
    async def _change_light(self, new_light_state: LightModel) -> (LightModel | HTTPError):
        """Actually changes the light's state using the Phillips Hue API."""
        url = f"{LightsPlugin.BASE_URL}/light/{new_light_state["id"]}"
        payload = {
            "on": {"on": new_light_state["is_on"]},
            "dimming": {"brightness": new_light_state["brightness"]},
            "color": {"xy": new_light_state["color"]}
        }
        try:
            async with AsyncClient(verify=False) as client:
                response = await client.put(url, headers=LightsPlugin.HEADERS, json=payload)
            
            response.raise_for_status()
            return new_light_state
        except HTTPError as e:
            return e


    async def _change_group(self, new_group_state: GroupModel) -> (GroupModel | HTTPError):
        """Actually changes the group's state using the Phillips Hue API."""
        url = f"{LightsPlugin.BASE_URL}/grouped_light/{new_group_state["id"]}"
        payload = {
            "on": {"on": new_group_state["is_on"]},
            "dimming": {"brightness": new_group_state["brightness"]},
            "color": {"xy": new_group_state["color"]}
        }
        try:
            async with AsyncClient(verify=False) as client:
                response = await client.put(url, headers=LightsPlugin.HEADERS, json=payload)

            response.raise_for_status()
            return new_group_state
        except HTTPError as e:
            return e
        
        
if __name__ == "__main__":
    import asyncio
    lights = [
        {"id": "a60e6289-7979-4036-b1d5-a3795efba4b3", "name": "bedroom-light-1", "is_on": True, "brightness": 100.0, "color": {"x": 0.3865, "y":0.3784}},
        {"id": "7ac12c9c-4bc3-4792-83e2-67e93fa9ea6f", "name": "bedroom-light-2", "is_on": True, "brightness": 100.0, "color": {"x": 0.3865, "y":0.3784}},
        {"id": "4e8a1e19-63a6-49dd-bc8d-4dbb703e1652", "name": "bedroom-light-3", "is_on": True, "brightness": 100.0, "color": {"x": 0.3865, "y":0.3784}}
    ]
    new_light = {"id": "a60e6289-7979-4036-b1d5-a3795efba4b3", "name": "bedroom-light-1", "is_on": True, "brightness": 100.0, "color": {"x": 0.3865, "y":0.3784}}
    
    groups = [
        {"id": "bac841b0-3881-4c55-ad41-15b3afa249aa", "name": "Sam's Bedroom", "is_on": True, "brightness": 100.0, "color": {"x": 0.3865, "y":0.3784}}
    ]
    new_group = {"id": "bac841b0-3881-4c55-ad41-15b3afa249aa", "name": "Sam's Bedroom", "is_on": True, "brightness": 100.0, "color": {"x": 0.3865, "y":0.3784}}
    
    
    
    lp = LightsPlugin(lights, groups)
    
    async def main():
        #print(await lp.change_light_state("a60e6289-7979-4036-b1d5-a3795efba4b3", new_light))
        print(await lp.change_group_state("bac841b0-3881-4c55-ad41-15b3afa249aa", new_group))
        
    asyncio.run(main())