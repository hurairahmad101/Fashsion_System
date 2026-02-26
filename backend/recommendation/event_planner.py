def event_planner(event_name, location, date, weather):
    return {
        "event": event_name,
        "recommended_outfit": "Formal traditional wear" if event_name.lower() == "wedding" else "Smart casual",
        "color_palette": ["Black", "Gold"],
        "weather_note": f"Expected weather: {weather}",
        "celebrity_inspiration": "Celebrity-inspired look"
    }
