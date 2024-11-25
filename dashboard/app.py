import ipyleaflet as L
from faicons import icon_svg
from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_widget
import folium

HI_coords = [20.7, -157.8583]
HNL_coords = [21.3187, -157.9225]
OGG_coords = [20.8986, -156.4305]  # Kahului Airport
LIH_coords = [21.9750, -159.3380]  # Lihue Airport
KOA_coords = [19.7388, -156.0456]  # Kona International Airport
ITO_coords = [19.7203, -155.0485]  # Hilo International Airport

# Create a Folium map and add markers
def create_folium_map():
    HI_map = folium.Map(location=HI_coords, zoom_start=7)
    folium.Marker(HNL_coords, tooltip='HNL').add_to(HI_map)
    folium.Marker(OGG_coords, tooltip='OGG').add_to(HI_map)
    folium.Marker(LIH_coords, tooltip='LIH').add_to(HI_map)
    folium.Marker(KOA_coords, tooltip='KOA').add_to(HI_map)
    folium.Marker(ITO_coords, tooltip='ITO').add_to(HI_map)
    return HI_map

## Define Functions

## Define a reactive calc

## Set up the data import

## Set up the page layout
ui.page_opts(title='Windspeeds over Airfields', fillable=True)
    # Sidebar with inputs
with ui.sidebar():
    ui.input_checkbox_group('airfields', 'Select Airfields', choices=['HNL', 'OGG', 'LIH', 'KOA', 'ITO'], selected=['HNL', 'OGG', 'LIH', 'KOA', 'ITO'])
    ui.hr()
    ui.input_slider('speed', 'Wind Speed', min=0, max=100, step=1, value=15)

    # Box for maps
# with ui.card():
#    ui.card_header('IpyLeaflet')
#    @render_widget
#    def map():
#        return L.Map(zoom=4, center=(0, 0))
    
with ui.card():
    ui.card_header('Folium')
    @render.ui
    def folium_map():
        return create_folium_map()

    
    # Box for wind speed