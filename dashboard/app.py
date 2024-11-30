from pathlib import Path

import pandas as pd
import geopandas as gpd

from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_widget

import ipyleaflet as ipyl
from ipyleaflet import Map, GeoData
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
    df_filtered = filtered_data()
    threshold = input.wind_threshold()
    df_above_threshold = df_filtered[df_filtered['wind_speed_10m:kn'] >= threshold]

    df_below_threshold = df_filtered[df_filtered['wind_speed_10m:kn'] < threshold]

    gdf_filtered = gpd.GeoDataFrame(
        folium_filter(), 
        geometry=gpd.points_from_xy(folium_filter().lon, folium_filter().lat), crs="EPSG:4326"
    )
    return df_above_threshold, df_below_threshold, gdf_filtered  

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
# Function to create the Folium map 
def create_map(): 
    bounds = [[df['lat'].min() - 1, df['lon'].min() - 1], [df['lat'].max() + 1, df['lon'].max() + 1]]
    m = folium.Map(center=airfield_coords["HNL"], zoom_start=15)
    # Add markers with conditional colors to the map
    for _, row in folium_filter().iterrows():
            threshold = input.wind_threshold()
            marker_color = get_marker_color(row['wind_speed_10m:kn'], threshold)
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=folium.Popup(row['nearest_airport'], max_width=300),
                icon=folium.Icon(color=marker_color)
            ).add_to(m)
    #markers = MarkerCluster(location=airfield_coords, title= "test title", name="test name")
    #marker_color = get_marker_color(csv_geodata["wind_speed_10m:kn"], input.wind_threshold())
    #folium.marker(location = geo_data, icon=folium.Icon(color=marker_color)).add_to(m)
    #m.add(geo_data)
    #m.add_layer(markers) 
    # Popup associated to a layer
    m.fit_bounds(bounds)

    return m

def get_marker_color(wind_speed, threshold):
    if wind_speed < threshold:
        return 'green'
    else:
        return 'red'
#------------------------------#
# User interface
#------------------------------#
ui.page_opts(title="Windspeeds Over Hawaiian Airfields", fillable=False) 
# Sidebar
#------------------------------#
with ui.sidebar(width=450):    
    ui.input_select("date", "Choose Date", choices=df['Date_Format'].unique().tolist())
    
    ui.input_slider('wind_threshold', 'Wind Speed Threshold', min=1, max=35, value=5)
    
    #ui.input_select("center", "Re-Center Map", choices=list(airfield_coords.keys()))

    ui.input_checkbox_group(
        "airfields",
        "Choose Airfields:",
        choices=df['nearest_airport'].unique().tolist(), selected=df['nearest_airport'].unique().tolist()
    )

    ui.hr()
    
    @render.ui
    def folio():
        return create_map()


# Main panel
#------------------------------#

with ui.layout_columns():
    with ui.card():
        ui.card_header("CAUTION: High Winds!")
        @render.data_frame
        def table_above():
            # Fetch from the reactive calc function
            df_above_threshold, df_below_threshold, gdf_filtered= reactive_calc_combined()
            return render.DataGrid(df_above_threshold)
        
    with ui.card():
        @render.ui
        def explorer():
            df_above_threshold, df_below_threshold, gdf_filtered = reactive_calc_combined()
            return gdf_filtered.explore(marker_kwds={"radius": 7},tooltip=True, tooltip_sticky=True, )
                                       
with ui.card():
    ui.card_header('Airfields Below Wind Threshold: Good to fly!')
    @render.data_frame
    def table_below():
        df_above_threshold, df_below_threshold, gdf_filtered = reactive_calc_combined()
        return render.DataGrid(df_below_threshold)
          
# Convert DataFrame to GeoDataFrame
csv_geodata = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326"
    )
           
@reactive.effect
def _():
    map.widget.center = airfield_coords[input.center()]
    
@reactive.calc
def filtered_data():
    FilterMatch = df_display["Date_Format"].isin([input.date()]) & df_display['nearest_airport'].isin(input.airfields())
    return df_display[FilterMatch] 

@reactive.calc
def filtered_gdf():
    GeoMatch = csv_geodata["Date_Format"].isin([input.date()]) & csv_geodata['nearest_airport'].isin(input.airfields())
    return csv_geodata[GeoMatch] 

gdf_filtered = gpd.GeoDataFrame(
        csv_geodata, 
        geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")

@reactive.calc
def folium_filter():
    FolioMatch = df["Date_Format"].isin([input.date()]) & df['nearest_airport'].isin(input.airfields())
    return df[FolioMatch] 

print("App loaded")