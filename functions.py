import folium
import pandas as pd
import ee
import datetime


#pulls data from Google sheetscond
def pull_sheet_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/160hgu9P2nK3TSYUS694bKlwcg_bpNDWax1WJKLg-Ex8/edit#gid=0"
    url_1 = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=')
    sheet_df = pd.read_csv(url_1, dtype=str)
    return sheet_df

 #"""Adds a method for displaying Earth Engine image tiles to folium map."""
def add_ee_layer(self, ee_image_object, vis_params, name):
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
        name=name,
        overlay=True,
        show=False,
        control=True
    ).add_to(self)

#function that turns the data into nice tables to be inserted into the FOlium popups
def popup_html(row, dataframe):
    i = row
    site=dataframe['Site'].iloc[i]
    basal=dataframe['Basal Area (ft^2)'].iloc[i]
    density=dataframe['Density (trees/acre)'].iloc[i]
    history=dataframe['Summary of History'].iloc[i]
    interest=dataframe['Things of Interest'].iloc[i]
    ele=dataframe['elv'].iloc[i]
    ndvi=dataframe['ndvi'].iloc[i]

    left_col_color = "#19a7bd"
    right_col_color = "#f2f0d3"

    html = """<!DOCTYPE html>
<html>
<head>
<h4 style="margin-bottom:10"; width="200px">{}</h4>""".format(site) + """
</head>
    <table style="height: 126px; width: 350px;">
<tbody>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">Basal Area (ft^2)</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(basal) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">Density (trees/acre)</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(density) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">Elevation (m)</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(ele) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">Brief History</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(history) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">Interesting Tidbit</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(interest) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">NDVI ABOSLUTE TRUTH</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(ndvi) + """
</tr>
</tbody>
</table>
</html>
"""
    return html


#turns ee sataliette image into ndvi image
def getNDVI(image):
        return image.normalizedDifference(['B5', 'B4'])

#gets ndvi values for sites
def ndvi_master(dataframe, ndvi_img):
    lon_list = dataframe['Long'].tolist()
    lat_list = dataframe['Lat'].tolist()
    site_list = []
    counter = 0
    for i in lon_list:
        site_list.append([float(lon_list[counter]), float(lat_list[counter])])
        counter = counter + 1
    locations = ee.List(site_list).map(lambda coords : ee.Feature(ee.Geometry.Point(coords).buffer(100)))
    mine_area = ee.FeatureCollection(locations)
    image_left = ndvi_img.clip(mine_area)
    #input and output are images
    mineMeansFeatures = image_left.reduceRegions(
        collection = mine_area,
        reducer = ee.Reducer.mean(),
        scale = 30,
        )
    gf = mineMeansFeatures.getInfo()

    ndvi_list = []
    gf2 = gf['features']
    for i in gf2:
        prop = i['properties']
        if prop:
            mean = prop['mean']
            ndvi_list.append(mean)
        else:
            ndvi_list.append('NaN')
    return ndvi_list

#gets elevation values for sites
def elv_master(dataframe, elv_img):
    elv_list = []
    for i in range(0,len(dataframe)):
        data_lat=float(dataframe.iloc[i]['Lat'])
        data_long=float(dataframe.iloc[i]['Long'])
        point = ee.Geometry.Point(data_long, data_lat)
        scale = 100
        elv_point = elv_img.sample(point, scale).first().get('elevation').getInfo()
        elv_list.append(elv_point)
    return elv_list

#adds data to dataframe
def add_data(dataframe, sat_img, elv_img):
    dataframe['ndvi'] = ndvi_master(dataframe, sat_img)
    dataframe['elv'] = elv_master(dataframe, elv_img)
    return dataframe

#adds marker one by one on the map
def make_map_w_markers(dataframe, elv_img, ndvi_img):
    #creates map w/ folium
    m = folium.Map(location=[45.5152, -122.6784], zoom_start=10)
    # Add Earth Engine drawing method to folium.
    folium.Map.add_ee_layer = add_ee_layer

    # Set visualization parameters for ground elevation and ndvi
    elv_vis_params = {
        'min': 0, 'max': 4000,
        'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']}
    ndviParams = {'min': 0,
                'max': 0.5,
                'palette': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#ffffbf', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850']}
    # Arrange layers inside a list (elevation, LST and land cover).
    ee_tiles = [elv_img, ndvi_img]

    # Arrange visualization parameters inside a list.
    ee_vis_params = [elv_vis_params, ndviParams]

    # Arrange layer names inside a list.
    ee_tiles_names = ['Elevation', 'NDVI']
    for i in range(0,len(dataframe)):
        name=dataframe.iloc[i]['Site']
        data_lat=float(dataframe.iloc[i]['Lat'])
        data_long=float(dataframe.iloc[i]['Long'])
        ndvi = float(dataframe.iloc[i]['ndvi'])
        labels=dataframe['Site'].iloc[i]
        html = popup_html(i, dataframe)
        test_pop = folium.Popup(folium.Html(html, script=True), max_width=300)
        folium.Marker(location=[data_lat, data_long], popup=test_pop,icon=folium.Icon(color='black', icon='tree', prefix='fa')).add_to(m)
    for tile, vis_param, name in zip(ee_tiles, ee_vis_params, ee_tiles_names):
        m.add_ee_layer(tile, vis_param, name)
    folium.LayerControl(collapsed = False).add_to(m)
    return m

def map_master():
    try:
        ee.Initialize()
    except Exception as e:
        ee.Authenticate()
        ee.Initialize()
    # Define a region of interest with a buffer zone of 100m.
    u_poi = ee.Geometry.Point(-122.561, 45.441)
    roi = u_poi.buffer(100)
    #defines timerange for getting the least cloudy image between now and 90 days ago
    i_date = (datetime.datetime.now() - datetime.timedelta(90)).strftime("%Y-%m-%d")
    f_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # Import the USGS ground elevation image.
    elv_img = ee.Image('USGS/SRTMGL1_003')
    #gets radiance image from landsat
    sat_img = ee.ImageCollection('LANDSAT/LC08/C02/T1_TOA').filterDate(i_date, f_date).filterBounds(u_poi).sort('CLOUD_COVER').first()
    ndvi_img = getNDVI(sat_img)
    sheet_df = pull_sheet_data()
    sheet_ndvi_df = add_data(sheet_df, ndvi_img, elv_img)

    #lanbd cover layer initiliziation and map initilization


    full_map = make_map_w_markers(sheet_ndvi_df, ndvi_img, ndvi_img)
    return full_map

