import requests
import xml.etree.ElementTree as ET
import base64
import pandas as pd
from shiny import reactive, render
from shiny.express import ui, input
from shinywidgets import render_widget


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
                timestamp = value.get("date")  # Ensure the correct attribute name is used
                val = value.text
                data.append({"latitude": lat, "longitude": lon, "parameter": name, "timestamp": timestamp, "value": val})
    return data

# Convert parsed data to DataFrame
def create_dataframe(data):
    df = pd.DataFrame(data)
    # Convert timestamp to datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


# Create a Table
def create_table():
    @render.text
    def table():
        data = fetch_meteomatics_data()
        parsed_data = parse_meteomatics_data(data)
        df = create_dataframe(parsed_data)
        return df.to_html()