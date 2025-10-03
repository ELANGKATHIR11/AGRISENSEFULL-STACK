import { useState, useEffect } from "react";

type WeatherState = { type: "sunny" | "rainy" | "cloudy" | "night"; tempC: number };

export default function useWeather3d() {
  const [weather, setWeather] = useState<WeatherState>({ type: "sunny", tempC: 25 });

  // Mock auto-cycling weather for demo purposes
  useEffect(() => {
    const types: WeatherState["type"][] = ["sunny", "cloudy", "rainy", "night"];
    let idx = 0;
    const t = setInterval(() => {
      idx = (idx + 1) % types.length;
      setWeather({ type: types[idx], tempC: 20 + Math.round(Math.random() * 10) });
    }, 18_000); // change every 18s for demo
    return () => clearInterval(t);
  }, []);

  return weather;
}
