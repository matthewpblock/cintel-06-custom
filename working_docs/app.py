from pathlib import Path

import pandas as pd
import geopandas as gpd

from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_widget

import ipyleaflet as ipyl
from ipyleaflet import Map, Marker, MarkerCluster, GeoData

#------------------------------#
# Airfield coords
#------------------------------#
airfield_coords = {
    "HNL": (21.3187, -157.9225),
    "OGG": (20.8986, -156.4305),
    "LIH": (21.9750, -159.3380),
    "KOA": (19.7388, -156.0456),
    "ITO": (19.7203, -155.0485)
}
# Extracting airport codes from airfield_coords
airports = list(airfield_coords.keys())


#------------------------------#
# Import data from CSV
#------------------------------#
infile = Path(__file__).parent / "custom_app_weather_data.csv"
df = pd.read_csv(infile, sep=';')
# Convert DataFrame to GeoDataFrame
csv_data = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.lon, df.lat)
    )
#------------------------------#
# Create the map
#------------------------------#
# Function to create the ipyleaflet map 
def create_map(): 
    m = Map(center=airfield_coords["HNL"], zoom=6)
    geo_data = GeoData(geo_dataframe = csv_data, name = 'Airfields')
    markers = MarkerCluster(location=airfield_coords)
    m.add(geo_data)
    m.add_layer(markers) 
    return m

#------------------------------#
# User interface
#------------------------------#
# Sidebar
#------------------------------#
with ui.sidebar():    
    ui.input_slider('wind_threshold', 'Wind Speed Threshold', min=1, max=165, value=15)
    
    ui.input_select("center", "Center", choices=list(airfield_coords.keys()))

    ui.input_checkbox_group(
        "airfields",
        "Choose Airfields:",
        airports,
    )
# Main panel
#------------------------------#

with ui.navset_card_underline():

    with ui.nav_panel("Data frame"):
        @render.data_frame
        def frame():
            # Give dat() to render.DataGrid to customize the grid
            return df

    with ui.nav_panel("Table"):
        @render.table
        def table():
            return csv_data

    with ui.nav_panel("Map"):
        @render_widget
        def map():
            return create_map()


@reactive.effect
def _():
    map.widget.center = airfield_coords[input.center()]
        
