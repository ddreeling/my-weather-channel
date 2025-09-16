"""
Goal: Download an hourly weather forecast for Cork from the free Open-Meteo API,
save the raw JSON to disk, turn the parts we care about into a tidy table
(temperature, precipitation, wind), and save that table as a CSV.
"""

# --- Standard library imports (come with Python) ---
import os               # Work with folders/files and paths
import json             # Read/write JSON text files
from datetime import datetime  # Convert text timestamps into datetime objects

# --- Third-party libraries (install with: pip install requests pandas) ---
import requests         # Make HTTP requests (call web APIs)
import pandas as pd     # Tabular data library (DataFrame)

# ------------------------- CONFIGURATION -------------------------
CITY = "Cork"                  # Just for file names and printing
LAT, LON = 51.8985, -8.4756    # Cork latitude/longitude
TIMEZONE = "Europe/Dublin"     # Controls how the API formats times

# Base URL for Open-Meteo. No API key is required (nice!).
# We ask for hourly: temperature, precipitation, wind speed at 10 m height.
# TIMEZONE must use URL encoding for the slash (/) → %2F.
URL = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&hourly=temperature_2m,precipitation,wind_speed_10m"
    f"&timezone={TIMEZONE.replace('/', '%2F')}"
)

# ------------------------- FILE LOCATIONS -------------------------
# We want to save files under a sibling "data" folder:
#   project_root/
#     your_script.py
#     data/  <-- we create this if it doesn't exist
#
# __file__ = path of THIS python file. os.path.dirname(__file__) = its folder.
# ".." moves one level up to the project root. Then we append "data".
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Create the data folder if it's not already there (no error if it exists).
os.makedirs(DATA_DIR, exist_ok=True)

# ------------------------- CALL THE API -------------------------
print(f"Fetching forecast for {CITY} ({LAT},{LON})…")

# Make the HTTP GET request.
# timeout=30 means: give up if the server doesn't respond within 30 seconds.
resp = requests.get(URL, timeout=30)

# If the server replied with an error code (e.g., 404 or 500), raise an error now.
resp.raise_for_status()

# Parse the response body (text) as JSON → Python dict/list structures.
raw = resp.json()

# ------------------------- SAVE RAW JSON -------------------------
# Useful for debugging and keeping the unmodified data.
raw_path = os.path.join(DATA_DIR, f"{CITY.lower()}_raw.json")

# Open the file for writing. encoding="utf-8" handles any special characters.
with open(raw_path, "w", encoding="utf-8") as f:
    # json.dump writes the Python object as nicely formatted JSON text.
    json.dump(raw, f, indent=2)

print(f"Saved raw JSON → {raw_path}")

# ------------------------- EXTRACT FIELDS -------------------------
# The API returns a big dictionary. The "hourly" section contains arrays
# that line up by index (same length, same order).
hourly = raw.get("hourly", {})  # {} default avoids crashes if key is missing
times = hourly.get("time", [])                  # ISO 8601 strings
temps = hourly.get("temperature_2m", [])        # Degrees Celsius
precip = hourly.get("precipitation", [])        # Millimetres (mm)
wind = hourly.get("wind_speed_10m", [])         # Metres per second (m/s)

# We'll build a list of rows (each row is a dict) and then make a DataFrame.
rows = []
for i in range(len(times)):
    # Convert the ISO timestamp text into a real datetime object for easier sorting/filtering.
    # If conversion fails for any reason, keep the original string.
    try:
        ts = datetime.fromisoformat(times[i])
    except Exception:
        ts = times[i]

    # Build one row. round(...) just makes the numbers look tidy.
    rows.append({
        "timestamp": ts,
        "temperature_c": round(float(temps[i]), 2),
        "precipitation_mm": round(float(precip[i]), 2),
        "wind_speed_mps": round(float(wind[i]), 2),  # m/s is the API default
    })

# Turn the list of dicts into a table.
df = pd.DataFrame(rows)

# Drop any rows with missing values (if the API had gaps) and sort by time.
df = df.dropna().sort_values("timestamp")

# ------------------------- SAVE CLEAN CSV -------------------------
clean_path = os.path.join(DATA_DIR, f"{CITY.lower()}_clean.csv")
df.to_csv(clean_path, index=False)  # index=False: don't write the DataFrame row numbers

print(f"Clean CSV saved → {clean_path}")

# Show the first 8 rows in the console as a quick preview.
print(df.head(8))
