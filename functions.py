import folium
import pandas as pd
import ee
import datetime

# returns a Dataframe containing class data from the Google sheet
def pull_sheet_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/160hgu9P2nK3TSYUS694bKlwcg_bpNDWax1WJKLg-Ex8/edit#gid=0"
    url_1 = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=')
    sheet_df = pd.read_csv(url_1, dtype=str)
    return sheet_df

# defines a method for converting ee Images to folium map layers
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

# converts Dataframe into html popups to add to map
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
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">ndvi</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(ndvi) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">Brief History</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(history) + """
</tr>
<tr>
<td style="background-color: """+ left_col_color +""";"><span style="color: #ffffff;">Interesting Tidbit</span></td>
<td style="width: 150px;background-color: """+ right_col_color +""";">{}</td>""".format(interest) + """
</tr>
</tbody>
</table>
</html>
"""
    return html

#converts ee sat Image into ndvi image
def getNDVI(image):
        return image.normalizedDifference(['B5', 'B4'])

#get the ndvi values for each site
def ndvi_master(ndvi_img, site_list):
    # creates an ee Image of random point samples in a 100m radius around each site

    locations = ee.List(site_list).map(lambda coords : ee.Feature(ee.Geometry.Point(coords).buffer(100)))
    study_area = ee.FeatureCollection(locations)
    image_left = ndvi_img.clip(study_area)
    #takes the mean ndvi value from the site point sample image
    sitesMeansFeatures = image_left.reduceRegions(
        collection = study_area,
        reducer = ee.Reducer.mean(),
        scale = 30,
        )
    #extracs the mean ndvi values from the ee FeatureCollection and adds tehm to a list
    gf = sitesMeansFeatures.getInfo()
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

# gets the elevation at each site
def elv_master(elv_img, site_list):
    elv_list = []
    counter = 0
    for i in site_list:
        point = ee.Geometry.Point(site_list[counter])
        scale = 100
        elv_point = elv_img.sample(point, scale).first().get('elevation').getInfo()
        elv_list.append(elv_point)
        counter = counter + 1
    return elv_list

# adds ndvi and elevation data to the dataframe
def add_data(dataframe, sat_img, elv_img, lon_list, lat_list):
    site_list = []
    counter = 0
    for i in lon_list:
        site_list.append([float(lon_list[counter]), float(lat_list[counter])])
        counter = counter + 1
    dataframe['ndvi'] = ndvi_master(sat_img, site_list)
    dataframe['elv'] = elv_master(elv_img, site_list)
    return dataframe

#adds different color map pins for different class years
def get_class_year_color(class_year):
    if int(''.join(filter(str.isdigit, class_year))) == 23:
        class_color = 'black'
        return class_color
    elif int(''.join(filter(str.isdigit, class_year))) == 24:
        class_color = 'blue'
        return class_color
    elif int(''.join(filter(str.isdigit, class_year))) == 25:
        class_color = 'red'
        return class_color
    else:
        class_color = 'green'
        return class_color

##creates Folium map, adds layers and markers
def make_map_w_markers(dataframe, elv_img, ndvi_img):
    # creates map, adds layer method to Folium maps, defines visual parameters for the layers
    m = folium.Map(location=[45.5152, -122.6784], zoom_start=10)
    folium.Map.add_ee_layer = add_ee_layer
    elv_vis_params = {
        'min': 0, 'max': 4000,
        'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']}
    ndviParams = {'min': 0,
                'max': 0.5,
                'palette': ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#ffffbf', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850']}
    ee_tiles = [elv_img, ndvi_img]
    ee_vis_params = [elv_vis_params, ndviParams]
    ee_tiles_names = ['Elevation', 'NDVI']
    # adds markers to map
    for i in range(0,len(dataframe)):
        name=dataframe.iloc[i]['Site']
        data_lat=float(dataframe.iloc[i]['Lat'])
        data_long=float(dataframe.iloc[i]['Long'])
        html = popup_html(i, dataframe)
        class_year = dataframe.iloc[i]['Class']
        class_color = get_class_year_color(class_year)
        test_pop = folium.Popup(folium.Html(html, script=True), max_width=300)
        folium.Marker(location=[data_lat, data_long], popup=test_pop,icon=folium.Icon(color=class_color, icon='tree', prefix='fa')).add_to(m)
    #adds layers to map
    for tile, vis_param, name in zip(ee_tiles, ee_vis_params, ee_tiles_names):
        m.add_ee_layer(tile, vis_param, name)
    folium.LayerControl(collapsed = False).add_to(m)
    return m

#gets sateliate images that cover full range of sites
def get_images(lon_list, lat_list):
    #defines time range for getting images from the last 90 days
    i_date = (datetime.datetime.now() - datetime.timedelta(90)).strftime("%Y-%m-%d")
    f_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # finds the exterior lines of latitude and longitude
    left_line=float(max(lon_list))
    right_line=float(min(lon_list))
    top_line=float(max(lat_list))
    bottom_line=float(min(lat_list))
    #creates points at the intersection of the exterior lat/lon lines. Essentially "draws a box" around the study sites
    top_left_corner =  ee.Geometry.Point(left_line, top_line)
    top_right_corner =  ee.Geometry.Point(right_line, top_line)
    bottom_left_corner =  ee.Geometry.Point(left_line, bottom_line)
    bottom_right_corner =  ee.Geometry.Point(left_line, bottom_line)
    #finds images that cover all four corners of the box and merges them together.
    # Not a perfect, or even a good soluton, but seemed a resonble compromise between
    # covering edge cases and making too many requests to the ee API
    sat_img_top_left = ee.ImageCollection('LANDSAT/LC08/C02/T1_TOA').filterDate(i_date, f_date).filterBounds(top_left_corner).sort('CLOUD COVER').first()
    sat_img_top_right = ee.ImageCollection('LANDSAT/LC08/C02/T1_TOA').filterDate(i_date, f_date).filterBounds(top_right_corner).sort('CLOUD COVER').first()
    sat_img_botttom_left = ee.ImageCollection('LANDSAT/LC08/C02/T1_TOA').filterDate(i_date, f_date).filterBounds(bottom_left_corner).sort('CLOUD COVER').first()
    sat_img_bottom_right = ee.ImageCollection('LANDSAT/LC08/C02/T1_TOA').filterDate(i_date, f_date).filterBounds(bottom_right_corner).sort('CLOUD COVER').first()
    sat_img_combined = ee.ImageCollection([sat_img_top_left, sat_img_top_right, sat_img_botttom_left, sat_img_bottom_right]).mosaic()
    return sat_img_combined

#puts everything together
def map_master():
    # uses service account to autheticate ee access
    service_account = "pitw-update@pitw-389420.iam.gserviceaccount.com"
    credentials = ee.ServiceAccountCredentials(service_account, "private-key.json")
    ee.Initialize(credentials)
    # gets data, analyizes it, and returns a list containing the completed map and a Dataframe with the ndvi and elevation values added
    sheet_df = pull_sheet_data()
    lon_list = sheet_df['Long'].tolist()
    lat_list = sheet_df['Lat'].tolist()
    sat_img_combined = get_images(lon_list, lat_list)
    elv_img = ee.Image('USGS/SRTMGL1_003')
    ndvi_img = getNDVI(sat_img_combined)
    sheet_ndvi_df = add_data(sheet_df, ndvi_img, elv_img, lon_list, lat_list)
    full_map = make_map_w_markers(sheet_ndvi_df, elv_img, ndvi_img)
    list_data_and_map = [full_map, sheet_df]
    return list_data_and_map

# creates Dataframe for summary data indexed by class
def data_master(data):
    data[['Basal Area (ft^2)', 'Density (trees/acre)', 'ndvi', 'elv']] = data[['Basal Area (ft^2)', 'Density (trees/acre)', 'ndvi', 'elv']].apply(pd.to_numeric, errors='coerce')
    summary_df = data.groupby("Class").mean(numeric_only=True)
    return (summary_df)
