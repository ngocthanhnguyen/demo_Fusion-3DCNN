import numpy as np
from data_config import *
import folium
import folium.plugins as plugins
from folium.plugins import TimeSliderChoropleth, TimestampedGeoJson

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

  def createColorSet(self, min_color, max_color):
    from branca.colormap import linear
    cmap = linear.Greens_09.scale(min_color, max_color)
    return cmap

  def createGeoJsonFeature(self, feature):
    print('> Creating GeoJSON features...')
    features = []
    for _, row in df.iterrows():
        feature = {
            'type': 'Feature',
            'geometry': {
                'type':'Point', 
                'coordinates':[row['Longitude'],row['Latitude']]
            },
            'properties': {
                'time': row['DatetimeBegin'].date().__str__(),
                'style': {'color' : row['color']},
                'icon': 'circle',
                'iconstyle':{
                    'fillColor': row['color'],
                    'fillOpacity': 0.8,
                    'stroke': 'true',
                    'radius': 7
                }
            }
        }
        print(feature)
        features.append(feature)
    return features
    
  def createBaseMap(self):
    m = folium.Map(location=self.relativeloc2Coordinate(MAP['center']), zoom_start=11.5)
    return m
    
  def createHeatMap(self, gdf, features, areaId):
    m = self.createBaseMap()
    # g = TimeSliderChoropleth(
    #     gdf.to_json(),
    #     styledict=styledict,

    # ).add_to(m)
    TimestampedGeoJson(
        {'type': 'FeatureCollection',
        'features': features}
        , period='P1M'
        , add_last_point=True
        , auto_play=True
        , loop=True
        , max_speed=1
        , loop_button=True
        , date_options='YYYY-MM-DD HH:mm:ss'
        , time_slider_drag_update=True
    ).add_to(m)
    m.save('00_map_congested_' + str(areaId) + '.html')
    
  
  