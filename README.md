# PITW Mapping Project

Howdy! This is a mapping application created to supplement the Place in the Woods Forest Ethnography assignment for ESM-444 Forest Ecology at Portland State University. Students input data collected during the course of the project to a Google Sheet (https://docs.google.com/spreadsheets/d/1jySQbxCzbiSPNtTG1xPxiIWVtjMeawwrdV_XUwHfWEE/edit?usp=sharing), the app preforms some rudimentary geospatial analysis on the sites using Google Earth Engine, and the resulting data is mapped, summarized, and displayed at (INSERT WEB SITE HERE)

I had only minimal previous experiance with programming and GIS prior to the outset of this project, no experiance with Python or any of the other technologies used, and highly  limited time. Therefore this project has a number of unfinished edges and is liable to break at any moment. The point was not necessarily to make something that "works": it was to learn how these things *work*.

If you are interested in adding something to the project, or if something breaks horribly and needs to be fixed, you can contact me at christopherburkelecompte@gmail.com.

___________________________________________________________________________________________
Things to Add, Fix, or Finese

Add:
-At the moment, the geospatial analysis does not integrate the student collected data in a meaningful way: it just takes the inputted coordinates and uses satellite images to approximate the ndvi at the sites. Putting together some sort of model using a combination of satellite images and student-collected "ground data" would be cool. For example, creating a statistical model that uses measurments of leaf area taken at the sites to validate the NDVI, and vice-versa, would a cool thing to know how to make.

-More interesting analysis and visualization of the summary data

Fix:
-It's sort of ugly

-Data cleaning measures. Currently, if someone puts in "bad data" (i.e. coordinates with a comma left in or something), there are no meaures in place to "clean" that data and make it usable.


Finese
-The current programatic method for aquiring sateliette images is somewhat haphazard (it draws a box around the lat/lon perimeter of the sites and pulls images that cover all four corners of the box). While this will probably work *most* of the time, its sort of a sloppy compenstation for the fact that I don't really know how to work with Earth Engine, and the images it pulls can be slightly suspect sometimes.

___________________________________________________________________________________________
Technologies Used

-Earth Engine Python API 0.1.353
-Python 3.11.3
-Flask 2.3.2
-Folium 0.14.0
-Pandas 2.0.1
