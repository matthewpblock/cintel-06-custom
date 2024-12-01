from pathlib import Path
import pandas as pd
import geopandas as gpd
from shiny import reactive
from shiny.express import input, render, ui
from ipyleaflet import Map, Marker, Popup, LayerGroup, basemaps
from ipywidgets import HTML
from shinywidgets import render_widget

#------------------------------#
# Airfield coordinates
#------------------------------#
# Dictionary containing airport codes and their coordinates
airfield_coords = {
    "HNL": (21.3187, -157.9225),  # Honolulu International Airport
    "OGG": (20.8986, -156.4305),  # Kahului Airport
    "LIH": (21.9750, -159.3380),  # Lihue Airport
    "KOA": (19.7388, -156.0456),  # Kona International Airport
    "ITO": (19.7203, -155.0485)   # Hilo International Airport
}

# Extracting airport codes from the dictionary
airports = list(airfield_coords.keys())

# Dictionary to map original column headers to more readable alternatives
column_rename_dict = {
    'validdate': 'DateTime',
    't_2m:F': 'Temp. (F)',
    'wind_speed_10m:kn': 'Wind Speed (kn)',
    'nearest_airport': 'Airport',
    'Date_Format': 'Day'
}

#------------------------------#
# Helper functions
#------------------------------#

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

#------------------------------#
# Import data from CSV
#------------------------------#
infile = Path(__file__).parent / "custom_app_weather_data.csv"
df = pd.read_csv(infile, sep=';')

# Convert the 'validdate' column to datetime type 
df['datetime'] = pd.to_datetime(df['validdate'], format='%Y-%m-%dT%H:%M:%SZ') 


# Extract the date part 
df['date'] = df['datetime'].dt.date
df['Day'] = df['datetime'].dt.strftime('%a-%b-%d')

df['Airport'] = df.apply(lambda row: find_nearest_airport(row['lat'], row['lon']), axis=1)

# Rename columns using the dictionary
df.rename(columns=column_rename_dict, inplace=True)

# Create Dataframe filters
#------------------------------#

# Reactive function to calculate filtered data and create GeoDataFrames
@reactive.calc()
def reactive_calc_combined():
    # Get the filtered data based on user inputs
    df_filtered = filtered_data()
    
    # Get the wind speed threshold from user input
    threshold = input.wind_threshold()
    
    # Filter data above the wind speed threshold
    df_above_threshold = df_filtered[df_filtered['Wind Speed (kn)'] >= threshold]
    
    # Filter data below the wind speed threshold
    df_below_threshold = df_filtered[df_filtered['Wind Speed (kn)'] < threshold]
    
    # Create a GeoDataFrame for the filtered data
    gdf_filtered = gpd.GeoDataFrame(
        folium_filter(), 
        geometry=gpd.points_from_xy(folium_filter().lon, folium_filter().lat), crs="EPSG:4326"
    )
    
    # Return the filtered DataFrames and GeoDataFrame
    return df_above_threshold, df_below_threshold, gdf_filtered  

# Create a display DataFrame with selected columns
df_display = df[['Day', 'Airport', 'Wind Speed (kn)', 'Temp. (F)']]

#------------------------------#
# Create the map
#------------------------------#
# Function to create the Folium map (commented out for ipyleaflet map, due to loading issues with ShinyLive and GitHub)
#def create_map(): 
    # Calculate the bounding box for the map based on the latitude and longitude of the data points
    #bounds = [[df['lat'].min() - 1, df['lon'].min() - 1], [df['lat'].max() + 1, df['lon'].max() + 1]]
    
    # Initialize the Folium map centered at Honolulu International Airport with a starting zoom level of 15
    #m = folium.Map(location=airfield_coords["HNL"], zoom_control=False, scrollWheelZoom=False)
    
    # Add markers with conditional colors to the map
    #for _, row in folium_filter().iterrows():
        # Get the wind speed threshold from user input
        #threshold = input.wind_threshold()
        
        # Determine the marker color based on the wind speed and threshold
        #marker_color = get_marker_color(row['Wind Speed (kn)'], threshold)
        
        # Add a marker to the map with the determined color
        #folium.Marker(
        #    location=[row['lat'], row['lon']],
        #    popup=folium.Popup(row['Airport'], max_width=300),
        #    icon=folium.Icon(color=marker_color)
        #).add_to(m)
    
    # Fit the map to the calculated bounds
    #m.fit_bounds(bounds)
    
    # Return the created map
    #return m
#------------------------------#
# New Ipyleaflet map
#------------------------------#
# Function to create the ipyleaflet map
def create_ipyleaflet_map():
    # Calculate the center of the map
    center = [df['lat'].mean(), df['lon'].mean()]
    
    # Initialize the ipyleaflet map
    m = Map(basemap=basemaps.Esri.WorldImagery, center=center, zoom=6)
    markers = LayerGroup()
    # Add markers to the map with conditional colors
    for _, row in folium_filter().iterrows():
        marker_color = get_marker_color(row['Wind Speed (kn)'], input.wind_threshold())
        marker = Marker(
            location=(row['lat'], row['lon']),
            title=row['Airport'],
            draggable=False,)
        markers.add(marker)
        
    m.add(markers)
    
    # Return the created map
    return m

# Function to determine the marker color based on wind speed and threshold
def get_marker_color(wind_speed, threshold):
    # If the wind speed is below the threshold, return 'green'
    if wind_speed < threshold:
        return 'green'
    # Otherwise, return 'red'
    else:
        return 'red'

#------------------------------#
# User interface
#------------------------------#
ui.page_opts(title="Windspeeds Over Hawaiian Airfields", fillable=False) 

# Sidebar
#------------------------------#
with ui.sidebar(width=450):    
    # Dropdown to select a date from the unique dates in the DataFrame
    ui.input_select("date", "Choose Date", choices=df['Day'].unique().tolist())
    
    # Slider to set the wind speed threshold
    ui.input_slider('wind_threshold', 'Wind Speed Threshold', min=1, max=35, value=5)
    
    # Checkbox group to select airfields from the unique nearest airports in the DataFrame
    ui.input_checkbox_group(
        "airfields",
        "Choose Airfields:",
        choices=df['Airport'].unique().tolist(), selected=df['Airport'].unique().tolist()
    )

    # Horizontal rule for visual separation
    ui.hr()
    
    # Render the Folium map
    #@render.ui
    #def folio():
    #    return create_map()
    
    #Ipyleaflet map
    @render_widget
    def leaflet():
        return create_ipyleaflet_map()

# Main panel
#------------------------------#

with ui.layout_columns():
    with ui.card():
        # Card header indicating high wind caution
        ui.card_header("CAUTION: High Winds!")
        
        @render.data_frame
        def table_above():
            # Fetch data from the reactive calc function
            df_above_threshold, df_below_threshold, gdf_filtered = reactive_calc_combined()
            # Return a DataGrid for data above the wind threshold
            return render.DataGrid(df_above_threshold)
        
    with ui.card(full_screen=True):
        @render.ui
        def explorer():
            # Fetch data from the reactive calc function
            df_above_threshold, df_below_threshold, gdf_filtered = reactive_calc_combined()
            # Return an interactive map for the filtered GeoDataFrame
            return gdf_filtered.explore(zoom_start=6, marker_kwds={"radius": 7}, tooltip=['Airport', 'lat', 'lon', 'Wind Speed (kn)', "Temp. (F)"], tooltip_sticky=True, highlight=True, min_zoom=4, max_zoom=12)
                                       
with ui.card():
    # Card header indicating airfields below wind threshold
    ui.card_header('Airfields Below Wind Threshold: Good to fly!')
    
    @render.data_frame
    def table_below():
        # Fetch data from the reactive calc function
        df_above_threshold, df_below_threshold, gdf_filtered = reactive_calc_combined()
        # Return a DataGrid for data below the wind threshold
        return render.DataGrid(df_below_threshold)
          
           
@reactive.calc
def filtered_data():
    # Filter the display DataFrame based on the selected date and nearest airports
    FilterMatch = df_display["Day"].isin([input.date()]) & df_display['Airport'].isin(input.airfields())
    # Return the filtered display DataFrame
    return df_display[FilterMatch] 

@reactive.calc
def folium_filter():
    # Filter the map DataFrame based on the selected date and nearest airports
    FolioMatch = df["Day"].isin([input.date()]) & df['Airport'].isin(input.airfields())
    # Return the filtered map DataFrame
    return df[FolioMatch] 

print("App loaded")