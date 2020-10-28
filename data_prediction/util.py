import numpy as np
from .data_config import *
from .Map import *
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
  
def export_predictive_map_sns(predicted, scale, areaId, outputPath):
  for frameId in range(predicted.shape[0]):
    pd = predicted[frameId, :, :, 0].astype(int)
    
    sns.heatmap(pd, vmin=0, vmax=scale, cbar=False, xticklabels=False, yticklabels=False, square=True, cmap='Reds')
    plt.savefig(outputPath + 'sns_frame' + str(frameId) + '_' + 'area' + str(areaId) + '.png')
    
def export_predictive_map_folium(predicted, areaId, outputPath):
  # prepare map
  map = Map()
  
  # prepare DataFrame to store traffic congestion info
  congestion_info = []
  for frameId in range(predicted.shape[0]):    
    pd = predicted[frameId, :, :, 0]
    congested_locations = np.argwhere(pd > 0)    
    for congested_location in congested_locations:
      congestion = [congested_location[0] + BOUNDARY_AREA[areaId][0], congested_location[1] + BOUNDARY_AREA[areaId][2]]
      if congestion[0] >= BOUNDARY_AREA[areaId][0] and congestion[0] <= BOUNDARY_AREA[areaId][1] and \
         congestion[1] >= BOUNDARY_AREA[areaId][2] and congestion[1] <= BOUNDARY_AREA[areaId][3]:
            congested_loc = map.relativeloc2Coordinate(congestion)

            # congestion_info = [timeStep areaCode congestedLength areaLatiude areaLongitude]
            congestion_info.append([frameId, '{:03d}{:03d}'.format(congestion[0],congestion[1]),\
                                   pd[congested_location[0], congested_location[1]], \
                                   congested_loc[0], congested_loc[1]])
  
  # prepare DataFrame which will be used to draw predictive maps
  minLength = 50
  df = pandas.DataFrame(congestion_info, columns=['time', 'area_id', 'congested_length', 'lat', 'lon'])
  df = df[df['congested_length'] >= minLength]
  cmap = map.createColorSet(minLength, df.congested_length.max())
  df['color'] = df['congested_length'].apply(cmap)
  
  # get predicted timestamps
  DATETIME = []
  filehandler = open('./00_data_output/predicted/time.csv', 'r')
  lines = filehandler.readlines()
  filehandler.close()
  for line in lines:
    if 's' not in line:
      DATETIME.append(line.strip())
    else:
      period = int(line.strip()[1:])
  # print('DATETIME:',DATETIME)
  
  # prepare data for predictive map
  geojsonFeatures = map.createGeoJsonFeatures(df, DATETIME)
  map.createPredictiveMap(geojsonFeatures, areaId, cmap, outputPath, period)

  