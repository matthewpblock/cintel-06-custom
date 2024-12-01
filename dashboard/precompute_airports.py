import pandas as pd
from geopy.distance import geodesic
from pathlib import Path


# Airfield coordinates
airfield_coords = {
    "HNL": (21.3187, -157.9225),
    "OGG": (20.8986, -156.4305),
    "LIH": (21.9750, -159.3380),
    "KOA": (19.7388, -156.0456),
    "ITO": (19.7203, -155.0485)
}

# Function to find the nearest airport based on latitude and longitude
def find_nearest_airport(lat, lon):
    min_distance = float('inf')
    nearest_airport = None
    for airport, coords in airfield_coords.items():
        distance = ((lat - coords[0])**2 + (lon - coords[1])**2)**0.5  # Euclidean distance
        if distance < min_distance:
            min_distance = distance
            nearest_airport = airport
    return nearest_airport

# Load the CSV data
infile = Path(__file__).parent / "custom_app_weather_data.csv"
df = pd.read_csv(infile, sep=';')

# Compute the nearest airport for each row
df['nearest_airport'] = df.apply(lambda row: find_nearest_airport(row['lat'], row['lon']), axis=1)

# Save the updated DataFrame to a new CSV file
df.to_csv("precomputed_weather_data.csv", index=False)