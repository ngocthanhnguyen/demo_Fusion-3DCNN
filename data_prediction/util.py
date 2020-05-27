import numpy as np
from data_config import *
from Map import *
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import Polygon
import geopandas
import pandas
from datetime import datetime

def print_historical_statistics(data):
  data_congestion     = np.sum(data['Input_congestion'] * MAX_FACTOR['Input_congestion'])
  data_rainfall       = np.sum(data['Input_rainfall']   * MAX_FACTOR['Input_rainfall'])
  data_accident       = np.sum(data['Input_accident']   * MAX_FACTOR['Input_accident'])    
  data_sns            = np.sum(data['Input_sns']        * MAX_FACTOR['Input_sns'])    
  
  data_sns = data_sns.astype(int)
  data_sns_congestion = np.zeros_like(data_sns)
  data_sns_rainfall = np.zeros_like(data_sns)
  data_sns_accident = np.zeros_like(data_sns)
  for msg_type in LINK_FACTOR['Input_congestion']:
      data_sns_congestion[data_sns == msg_type] = 1
  for msg_type in LINK_FACTOR['Input_rainfall']:
      data_sns_rainfall[data_sns == msg_type] = 1
  for msg_type in LINK_FACTOR['Input_accident']:
      data_sns_accident[data_sns == msg_type] = 1
  data_sns_congestion = np.sum(data_sns_congestion)
  data_sns_rainfall = np.sum(data_sns_rainfall)
  data_sns_accident = np.sum(data_sns_accident)
  
  print('data_congestion:', data_congestion)
  print('data_rainfall:', data_rainfall)
  print('data_accident:', data_accident)
  print('data_sns_congestion:', data_sns_congestion)
  print('data_sns_rainfall:', data_sns_rainfall)
  print('data_sns_accident:', data_sns_accident)
  
def print_preditive_acc(gt, pd):
  gt_congestion       = ytest['default']      * MAX_FACTOR['Input_congestion']
  pd_congestion       = ypredicted            * MAX_FACTOR['Input_congestion']
  gt_congestion       = np.reshape(gt_congestion, (1, -1))
  pd_congestion       = np.reshape(pd_congestion, (1, -1))

  error_MSE           = mse(gt_congestion, pd_congestion)
  error_MAE           = mae(gt_congestion, pd_congestion)
  error_RMSE          = rmse(gt_congestion, pd_congestion)
  
def export_predictive_map_sns(predicted, scale, areaId):
  for frameId in range(predicted.shape[0]):
    pd = predicted[frameId, :, :, 0].astype(int)
    
    sns.heatmap(pd, vmin=0, vmax=scale, cbar=False, xticklabels=False, yticklabels=False, square=True, cmap='Reds')
    plt.savefig('00_frame' + str(frameId) + '_' + 'area' + str(areaId) + '.png')
    
def export_predictive_map_folium(predicted, areaId):
  # prepare map
  map = Map()
  
  # prepare HeatMapWithTime
  congestion_info = []
  congested_areas = []
  for frameId in range(predicted.shape[0]):
    
    pd = predicted[frameId, :, :, 0]
    congested_locations = np.argwhere(pd > 0)    
    for congested_location in congested_locations:
      congestion = [congested_location[0] + BOUNDARY_AREA[areaId][0], congested_location[1] + BOUNDARY_AREA[areaId][2]]
      if congestion[0] >= BOUNDARY_AREA[areaId][0] and congestion[0] <= BOUNDARY_AREA[areaId][1] and \
         congestion[1] >= BOUNDARY_AREA[areaId][2] and congestion[1] <= BOUNDARY_AREA[areaId][3]:
            # congested_area = [map.relativeloc2Coordinate([congestion[0]-5, congestion[1]-5]), \
            #                   map.relativeloc2Coordinate([congestion[0]-5, congestion[1]+5]), \
            #                   map.relativeloc2Coordinate([congestion[0]+5, congestion[1]+5]), \
            #                   map.relativeloc2Coordinate([congestion[0]+5, congestion[1]-5]), \
            #                   map.relativeloc2Coordinate([congestion[0]-5, congestion[1]-5])
            #                  ]
            # congested_area = Polygon(zip(map.separateCoordinates(congested_area)[0], map.separateCoordinates(congested_area)[1]))
            congested_loc = map.relativeloc2Coordinate(congestion)

            congestion_info.append([frameId, '{:03d}{:03d}'.format(congestion[0],congestion[1]),\
                                   pd[congested_location[0], congested_location[1]], \
                                   congested_loc[0], congested_loc[1]])
            # congested_areas.append(congested_area)
  
  # create dataframe
  df = pandas.DataFrame(congestion_info, columns=['time', 'area_id', 'congested_length', 'lat', 'lon'])
  # gdf = geopandas.GeoDataFrame(df, geometry=congested_areas)
  gdf = df
  print(gdf.head())
  
  # prepare styledict
  # datetime_index = pandas.date_range('2016-1-1', periods=6, freq='M')
  # dt_index_epochs = datetime_index.astype(int) // 10**9
  # dt_index = dt_index_epochs.astype('U10')
  # min = df.congested_length.min()
  # max_color = df.congested_length.max()  
  # print(min_color, max_color)
  # opacity = .5
  # areas = np.unique(df.area_id.values).tolist()
  # styledata = {}
  # for area in areas:    
  #   congestion_info = []
    
  #   for frameId in range(predicted.shape[0]):
  #     try:
  #       congested_length = df.loc[(df.area_id == area) & (df.time == frameId)]
  #       congested_length = congested_length.congested_length.values[0]
  #     except:
  #       congested_length = 0
      
  #     congestion_info.append([congested_length, opacity])
    
  #   dfStyle = pandas.DataFrame(congestion_info, columns = ('color', 'opacity'), index=dt_index)
  #   styledata[area] = dfStyle
  
  # max_color, min_color, max_opacity, min_opacity = 0, 0, 0, 0
  # for area, data in styledata.items():
  #   max_color = max(max_color, data['color'].max())
  #   min_color = min(max_color, data['color'].min())
  from branca.colormap import linear
  cmap = linear.Reds_09.scale(df.congested_length.min(), df.congested_length.max())
  
  df['color'] = df['congested_length'].apply(cmap)
  print(df.head())

  DATETIME = ['2015-07-01 08:00:00', '2015-07-01 12:00:00', '2015-07-01 16:00:00', \
              '2015-07-01 20:00:00', '2015-07-02 00:00:00', '2015-07-02 04:00:00']
  
  

  features = []
  for _, row in df.iterrows():
      feature = {
          'type': 'Feature',
          'geometry': {
              'type':'Point', 
              'coordinates':[row['lon'],row['lat']]
          },
          'properties': {
              'time': str(datetime.strptime(DATETIME[row['time']], '%Y-%m-%d %H:%M:%S')),
              'style': {'color' : row['color']},
              'icon': 'circle',
              'iconstyle':{
                  'fillColor': row['color'],
                  'fillOpacity': 1,
                  'stroke': 'true',
                  'radius': 7
              }
          }
      }
      print(feature)
      features.append(feature)
  
  # for area, data in styledata.items():
  #   data['color'] = data['color'].apply(cmap)
  #   data['opacity'] = data['opacity']


  # styledict = {
  #     area: data.to_dict(orient='index') for area, data in styledata.items()
  # }
  # print(gdf.to_json())
  
  # create map
  map.createHeatMap(gdf, features, areaId)

  