import requests
import xml.etree.ElementTree as ET
import base64
import pandas as pd
from shiny import reactive, render
from shiny.express import ui
from shinywidgets import render_widget

import folium
from folium.plugins import TimeSliderChoropleth

# Coordinates for airports
HI_coords = [20.7, -157.8583]
HNL_coords = [21.3187, -157.9225]
OGG_coords = [20.8986, -156.4305]  # Kahului Airport
LIH_coords = [21.9750, -159.3380]  # Lihue Airport
KOA_coords = [19.7388, -156.0456]  # Kona International Airport
ITO_coords = [19.7203, -155.0485]  # Hilo International Airport

# Fetch data from Meteomatics API
def fetch_meteomatics_data():
    url = "https://api.meteomatics.com/2024-11-24T21:35:00.000-10:00--2024-12-09T21:35:00.000-10:00:PT5M/t_2m:F,wind_speed_10m:kn/19.743906,-156.042296+19.7188306,-155.0475539+20.8956979,-156.4340476+21.32452,-157.92507+21.9720658,-159.3367154/xml?model=mix"
    username = "student_block_matthew"  # Replace with your Meteomatics API username
    password = "2Y1Vju9s9E"  # Replace with your Meteomatics API password
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Error {response.status_code}: {response.text}")
        response.raise_for_status()

# Parse the XML data
def parse_meteomatics_data(xml_data):
    root = ET.fromstring(xml_data)
    data = []
    for location in root.findall(".//location"):
        lat = location.get("latitude")
        lon = location.get("longitude")
        for parameter in location.findall(".//parameter"):
            name = parameter.get("name")
            for value in parameter.findall(".//value"):
                timestamp = value.get("datetime")
                val = value.text
                data.append({"latitude": lat, "longitude": lon, "parameter": name, "timestamp": timestamp, "value": val})
    return data

# Convert parsed data to DataFrame
def create_dataframe(data):
    df = pd.DataFrame(data)
    return df

# Create a Folium map and add markers
def create_folium_map():
    HI_map = folium.Map(location=HI_coords, zoom_start=7)
    folium.Marker(HNL_coords, tooltip='HNL').add_to(HI_map)
    folium.Marker(OGG_coords, tooltip='OGG').add_to(HI_map)
    folium.Marker(LIH_coords, tooltip='LIH').add_to(HI_map)
    folium.Marker(KOA_coords, tooltip='KOA').add_to(HI_map)
    folium.Marker(ITO_coords, tooltip='ITO').add_to(HI_map)
    return HI_map

# Fetch and parse data
try:
    xml_data = fetch_meteomatics_data()
    parsed_data = parse_meteomatics_data(xml_data)
    df = create_dataframe(parsed_data)
    print(df.head())  # Print the first few rows of the DataFrame for verification
except requests.exceptions.HTTPError as err:
    print(f"HTTP error occurred: {err}")

# Create a dictionary to map airport codes to their coordinates
airport_coords = {
    "HNL": (21.3187, -157.9225),
    "OGG": (20.8986, -156.4305),
    "LIH": (21.9750, -159.3380),
    "KOA": (19.7388, -156.0456),
    "ITO": (19.7203, -155.0485)
}

# Create a Folium map and add markers dynamically
def create_folium_map():
    HI_map = folium.Map(location=[20.7, -157.8583], zoom_start=7)
    for code, coords in airport_coords.items():
        folium.Marker(coords, tooltip=code).add_to(HI_map)
    return HI_map

# Define a reactive calc
@reactive.calc()
def reactive_calc_combined():
    # Your reactive calculation logic here
    pass

# Set up the page layout
ui.page_opts(title='Windspeeds over Airfields', fillable=True)

# Sidebar with inputs
with ui.sidebar():
    ui.sidebar_header('Settings')
    ui.input_checkbox_group('airports', 'Airports', ['HNL', 'OGG', 'LIH', 'KOA', 'ITO'], value=['HNL', 'OGG', 'LIH', 'KOA', 'ITO'])
    ui.hr()
    ui.input_slider('speed', 'Wind Speed', min=0, max=100, step=1, value=15)

# Main content
with ui.card():
    ui.card_header('Folium Map')
    @render.ui
    def folium_map():
        return create_folium_map()

# Display DataFrame in a table


# Box for wind speed