from typing import TypedDict, Annotated, List, Optional
from semantic_kernel.functions import kernel_function
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta

import os
from dotenv import load_dotenv
load_dotenv()

class WeatherDesc(TypedDict):
    name: str
    desc: str
    low: int
    high: int
    current_temp: int
    feels_like: int
    

class WeatherPlugin:
    BASE = "https://api.openweathermap.org/data/2.5"
    CURRENT_WEATHER_ENDPOINT = f"{BASE}/weather?"
    FORECAST_ENDPOINT = f"{BASE}/forecast?"
    API_KEY = os.getenv("OPEN_WEATHER_MAP_API_KEY")
    
    async def get_low_and_high(self, city: str) -> tuple[int, int]:
        async with AsyncClient() as client:
            response = await client.get(WeatherPlugin.FORECAST_ENDPOINT + f"q={city}&appid={WeatherPlugin.API_KEY}&units=imperial")
            data = response.json()
        
        tz_offset = data["city"]["timezone"]
        local_tz = timezone(timedelta(seconds=tz_offset))
        
        now_local = datetime.now(local_tz)            
        today = now_local.strftime("%Y-%m-%d")
        
        today_temps = []
        for entry in data["list"]:
            utc_time = datetime.strptime(entry["dt_txt"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            local_time = utc_time.astimezone(local_tz)
            
            if local_time.strftime("%Y-%m-%d") == today:
                today_temps.append(entry["main"]["temp"])
                
        return (int(min(today_temps)), int(max(today_temps)))
    
    @kernel_function
    async def get_weather_info(self, city: Annotated[str, "The city to get the weather data from"]) -> Optional[WeatherDesc]:
        async with AsyncClient() as client:
            response = await client.get(WeatherPlugin.CURRENT_WEATHER_ENDPOINT + f"q={city}&appid={WeatherPlugin.API_KEY}&units=imperial")
            data = response.json()
            
        low, high = await self.get_low_and_high(city)
            
        weather_desc = WeatherDesc(
            name=data['name'],
            desc=data['weather'][0]['description'],
            low=low,
            high=high,
            current_temp=int(data['main']['temp']),
            feels_like=int(data['main']['feels_like']),
        )
        
        return weather_desc
        
    
    
if __name__ == "__main__":
    import asyncio
    
    wp = WeatherPlugin()
    
    async def main():
        print(await wp.get_weather_info("New York"))
        
    asyncio.run(main())