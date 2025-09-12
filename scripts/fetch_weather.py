import os, json, requests
import pandas as pd
from datetime import datetime

# --- Config ---
CITY = "Cork"
LAT, LON = 51.8985, -8.4756   # Cork coordinates
TIMEZONE = "Europe/Dublin"

# Open-Meteo free weather API (no key required)
URL = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&hourly=temperature_2m,precipitation,wind_speed_10m"
    f"&timezone={TIMEZONE.replace('/', '%2F')}"
)

# Make sure /data exists
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

print(f"Fetching forecast for {CITY} ({LAT},{LON})…")
resp = requests.get(URL, timeout=30)
resp.raise_for_status()
raw = resp.json()

# Save raw JSON
raw_path = os.path.join(DATA_DIR, f"{CITY.lower()}_raw.json")
with open(raw_path, "w", encoding="utf-8") as f:
    json.dump(raw, f, indent=2)
print(f"Saved raw JSON → {raw_path}")

# Extract + clean
hourly = raw.get("hourly", {})
times = hourly.get("time", [])
temps = hourly.get("temperature_2m", [])
precip = hourly.get("precipitation", [])
wind = hourly.get("wind_speed_10m", [])

rows = []
for i in range(len(times)):
    try:
        ts = datetime.fromisoformat(times[i])
    except Exception:
        ts = times[i]
    rows.append({
        "timestamp": ts,
        "temperature_c": round(float(temps[i]), 2),
        "precipitation_mm": round(float(precip[i]), 2),
        "wind_speed_mps": round(float(wind[i]), 2),
    })

df = pd.DataFrame(rows).dropna().sort_values("timestamp")

# Save clean CSV
clean_path = os.path.join(DATA_DIR, f"{CITY.lower()}_clean.csv")
df.to_csv(clean_path, index=False)
print(f"Clean CSV saved → {clean_path}")
print(df.head(8))
