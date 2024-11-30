from pathlib import Path

import pandas as pd
import geopandas as gpd

from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_widget

import ipyleaflet as ipyl
from ipyleaflet import Map, Marker, MarkerCluster, GeoData, Popup
from geopy.distance import geodesic
from ipywidgets import HTML

import folium
import matplotlib
import mapclassify

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

# Function to find the nearest airport
def find_nearest_airport(lat, lon):
    min_distance = float('inf')
    nearest_airport = None
    for airport, coords in airfield_coords.items():
        distance = geodesic((lat, lon), coords).miles
        if distance < min_distance:
            min_distance = distance
            nearest_airport = airport
    return nearest_airport

#------------------------------#
# Import data from CSV
#------------------------------#
infile = Path(__file__).parent / "custom_app_weather_data.csv"
df = pd.read_csv(infile, sep=';')
# Convert DataFrame to GeoDataFrame
csv_geodata = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326"
    )
# Convert the 'validdate' column to datetime type 
df['datetime'] = pd.to_datetime(df['validdate'], format='%Y-%m-%dT%H:%M:%SZ') 


# Extract the date part 
df['date'] = df['datetime'].dt.date
unique_dates = str(df['date'].unique())
df['Date_Format'] = df['datetime'].dt.strftime('%a-%b-%d')
date_list = df['Date_Format']

df['nearest_airport'] = df.apply(lambda row: find_nearest_airport(row['lat'], row['lon']), axis=1)

# Create Dataframe filters
#------------------------------#

@reactive.calc()
def reactive_calc_combined():
    threshold = input.wind_threshold()
    df_above_threshold = df_display[df_display['wind_speed_10m:kn'] >= threshold]

    df_below_threshold = df_display[df_display['wind_speed_10m:kn'] < threshold]
    return df_above_threshold, df_below_threshold   

@reactive.Effect
def update_date_choices():
    unique_dates = df['date'].unique()
    input_date_choices = unique_dates.tolist()
    return input_date_choices

df_display = df[['Date_Format', 'nearest_airport', 'wind_speed_10m:kn', 't_2m:F']]

#def highlight_above_threshold(val):
#    color = 'red' if val > input.wind_threshold() else ''
#    return f'background-color: {color}'

#df_display = df_display.style.applymap(highlight_above_threshold, subset=['wind_speed_10m:kn'])
#------------------------------#
# Create the map
#------------------------------#
# Function to create the ipyleaflet map 
def create_map(): 
    m = Map(center=airfield_coords["HNL"], zoom=6, close_popup_on_click=False)
    geo_data = GeoData(geo_dataframe = csv_geodata, name = 'Airfields')
    #markers = MarkerCluster(location=airfield_coords, title= "test title", child=popup_message)
    #popup_message = HTML()
    #popup_message.value = "Hello <b>World</b>"
    #markers.popup = popup_message
    #popup_message.placeholder = "Some HTML"
    #popup_message.description = "Some HTML"

    m.add(geo_data)
    #m.add_layer(markers) 
    # Popup associated to a layer
    return m

#------------------------------#
# User interface
#------------------------------#
# Sidebar
#------------------------------#
with ui.sidebar():    
    ui.input_slider('wind_threshold', 'Wind Speed Threshold', min=1, max=35, value=5)
    
    #ui.input_select("center", "Re-Center Map", choices=list(airfield_coords.keys()))

    ui.input_checkbox_group(
        "airfields",
        "Choose Airfields:",
        airports, selected=airports
    )
    
    ui.input_select("date", "Choose Date", choices=df['Date_Format'].unique().tolist())
    
    ui.hr()
    
    @render.ui
    def sidebar_explorer():
        return csv_geodata.explore(marker_kwds={"radius": 7},tooltip=True, tooltip_sticky=True, )


# Main panel
#------------------------------#

with ui.navset_card_underline():

    with ui.nav_panel("Above Data frame"):
        @render.data_frame
        def table_above():
            # Fetch from the reactive calc function
            df_above_threshold, df_below_threshold = reactive_calc_combined()
            return render.DataGrid(df_above_threshold)

    with ui.nav_panel("Map"):
        @render_widget
        def map():
            return create_map()
        
    with ui.nav_panel("Explore"):
        @render.ui
        def explorer():
            return csv_geodata.explore(marker_kwds={"radius": 7},tooltip=True, tooltip_sticky=True, )

    with ui.nav_panel("Folium"):
        @render_widget
        def folio():
            return create_map()

with ui.card():
    @render.data_frame
    def table_below():
        df_above_threshold, df_below_threshold = reactive_calc_combined()
        return render.DataGrid(df_below_threshold)

@reactive.effect
def _():
    map.widget.center = airfield_coords[input.center()]
    
@reactive.effect
def date_choices():
    input_date_choices = df['Date_Format'].unique()
    return ("date", {"choices": list(unique_dates)})


print("App loaded")