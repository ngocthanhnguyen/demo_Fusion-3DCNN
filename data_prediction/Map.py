import numpy as np
from .data_config import *
import folium
import folium.plugins as plugins
from folium.plugins import TimeSliderChoropleth, TimestampedGeoJson
from datetime import datetime
from pathlib import Path

class Map:
  def __init__(self):
    pass
    
  def relativeloc2Coordinate(self, relative_location):
    relativeloc_start = [MAP['total_map']['size']['h'] - MAP['studied_map']['start']['lat'], \
                         0 + MAP['studied_map']['start']['lon']]

    relativeloc = [relativeloc_start[0] - relative_location[0], \
                   relativeloc_start[1] + relative_location[1]]
    
    coordinate = [MAP['coordinate']['start']['lat'] + MAP['coordinate']['offset']['lat']*relativeloc[0], \
                  MAP['coordinate']['start']['lon'] + MAP['coordinate']['offset']['lon']*relativeloc[1]]
    
    return coordinate
    
  def separateCoordinates(self, coordinates):
    lats = []
    lons = []
    
    for coordinate in coordinates:
      lats.append(coordinate[0])
      lons.append(coordinate[1])
      
    return [lats, lons]
    
  def loc2list(self,item,lenRelativeloc=3):
    y = int(item[-lenRelativeloc:])
    x = int(item[:len(item)-lenRelativeloc])
    location = [x,y]
    return location

  def createColorSet(self, min_length, max_length):
    from branca.colormap import linear
    cmap = linear.Reds_09.scale(min_length, max_length)
    cmap.caption = 'Độ dài kẹt xe trung bình (đo bằng mét)'
    return cmap

  def createGeoJsonFeatures(self, df, time_array):
    features = []
    for _, row in df.iterrows():
      feature = {
          'type': 'Feature',
          'geometry': {
              'type':'Point', 
              'coordinates':[row['lon'],row['lat']]
          },
          'properties': {
              'time': str(datetime.strptime(time_array[row['time']], '%Y-%m-%d %H:%M:%S')),
              'style': {'color' : row['color']},
              'icon': 'circle',
              'iconstyle':{
                  'fillColor': row['color'],
                  'fillOpacity': .5,
                  'stroke': 'true',
                  'radius': 125,
                  'opacity' : 1,
                  'lineCap' : 'square',
                  'lineJoin' : 'square'
              }
          }
      }
      features.append(feature)
  
    return features
    
  def createBaseMap(self, areaId):
    m = folium.Map(location=self.relativeloc2Coordinate(MAP['center']['zone' + str(areaId+1)]), zoom_start=12.7)
    return m
    
  def createPredictiveMap(self, features, areaId, cmap, outputPath, period_str):
    if period_str == 40000:
      period_set = 'PT4H'
    elif period_str == 6000:
      period_set = 'PT1H'
    elif period_str == 3000:  
      period_set = 'PT30M'
    htmlFile = outputPath + 'map_congested_' + str(areaId) + '.html'
    m = self.createBaseMap(areaId)
    TimestampedGeoJson(
        {'type': 'FeatureCollection',
        'features': features}
        , transition_time=1000
        , period=period_set
        , add_last_point=True
        , auto_play=True
        , loop=True
        , max_speed=1
        , loop_button=True
        , date_options='YYYY-MM-DD HH:mm:ss'
        , time_slider_drag_update=False
    ).add_to(m)
    m.add_child(cmap)
    m.save(htmlFile)
    
    self.beautifyDisplay(htmlFile)
    
  def beautifyDisplay(self, htmlFile):
    fileHandler = Path(htmlFile)
    
    # to draw circle which correspond to real-life radius
    fileHandler.write_text(fileHandler.read_text().replace('return new L.circleMarker(latLng, feature.properties.iconstyle)', 'return new L.circle(latLng, feature.properties.iconstyle)'))
    
    # change position of cmap
    fileHandler.write_text(fileHandler.read_text().replace('topright', 'bottomleft'))
  
  