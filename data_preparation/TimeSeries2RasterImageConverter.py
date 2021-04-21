## Importing the libraries
import numpy as np
import os
from .data_utils import DataParser, DataReader, DataScaler
from .jpmesh import jpmesh
from .config import *

class TimeSeries2RasterImageConverter:
  def __init__(self):
    self.dp = DataParser.DataParser()
    self.ds = DataScaler.DataScaler()
    
  def convert(self, data_file, starting_time, offset, num_steps):
    # read and parse data
    self.dr = DataReader.DataReader(data_file, DATA_READ['idx'])
    self.dr.read(delimiter='\t')
    data = self.dr.getData()
    data = self._parse_data(data)
    
    # convert to raster images and save
    i = 1
    while True:
      raster_img = self._generate_factor_map(data, starting_time)
      self._dump_factor(WD['output']['extract_raster'] + str(starting_time), raster_img)
      print('TimeSeries2RasterImageConverter:', WD['output']['extract_raster'] + str(starting_time))
      i += 1
      if i > num_steps:
        break
      starting_time = self._determine_next_time(starting_time, offset)
      

  def _parse_data(self, data):
    # datetime
    data = self.dp.removeDelimiters(data, DATA_READ['name'].index('datetime'), ('-', ' ', ':', '+09'))    
    data = self.dp.convertInt(data, DATA_READ['name'].index('datetime'))

    # list factors    
    data = self.dp.countElements(data, DATA_READ['name'].index('numsegments'), ',')

    # integer factors
    data = self.dp.convertInt(data, DATA_READ['name'].index('meshcode'))
    data = self.dp.convertInt(data, DATA_READ['name'].index('rainfall'))
    data = self.dp.convertInt(data, DATA_READ['name'].index('congestion'))

    # BoW SNS
    data = self.dp.removeDelimiters(data, DATA_READ['name'].index('sns'), ('{', '}'))
    data = self.dp.convertBoWType(data, DATA_READ['name'].index('sns'), SNS_COMPLAINTS)
    
    return data
     
  def _generate_factor_map(self, data, curr_time):
    loc = {}

    indices_time = np.argwhere(data[:, DATA_READ['name'].index('datetime')] == curr_time).tolist()
    factor_map = np.zeros((RASTER_CONFIG['width'], RASTER_CONFIG['height'],RASTER_CONFIG['num_factors']))
    for index_time in indices_time:
      j = index_time[0]

      # get center coordination of each mesh
      meshcode = data[j, DATA_READ['name'].index('meshcode')]
      mesh = jpmesh.parse_mesh_code(str(meshcode))
      mesh_center = mesh.south_west + (mesh.size / 8.0)
      latitude = mesh_center.lat.degree
      longitude = mesh_center.lon.degree

      # calculate relative positive on raster image
      loc['x'] = int((latitude - RASTER_CONFIG['start_lat']) // RASTER_CONFIG['offset_lat'])
      loc['y'] = int((longitude - RASTER_CONFIG['start_long']) // RASTER_CONFIG['offset_long'])

      if loc['x'] >= RASTER_CONFIG['width'] or loc['y'] >= RASTER_CONFIG['height']:
          j += 1
          continue
      
      # assign sensing data to corresponding location on raster image
      congestion = data[j, DATA_READ['name'].index('congestion')] 
      rainfall = data[j, DATA_READ['name'].index('rainfall')]
      accident = data[j, DATA_READ['name'].index('accident')]  
      if isinstance(accident, str) == True:
          accident = 1          
      if accident > 0:
          accident = 1

      sns      = data[j, DATA_READ['name'].index('sns')]

      factor_map[loc['x'] ,loc['y'],RASTER_CONFIG['congestion_channel']]  = congestion
      factor_map[loc['x'] ,loc['y'],RASTER_CONFIG['rainfall_channel']]    = rainfall
      factor_map[loc['x'] ,loc['y'],RASTER_CONFIG['accident_channel']]    = accident
      factor_map[loc['x'] ,loc['y'],RASTER_CONFIG['sns_channel']]         = sns

    factor_map = np.flip(factor_map, axis=0)
    return factor_map

  def _dump_factor(self, path, factor_map):
    np.savez_compressed(path, factor_map)

  def _determine_next_time(self, curr_time, offset):
    next_time = curr_time + offset
    
    SS = next_time % 100
    next_time //= 100
    MM = next_time % 100
    next_time //= 100
    HH = next_time % 100
    next_time //= 100
    dd = next_time % 100
    next_time //= 100
    mm = next_time % 100
    next_time //= 100
    yyyy = next_time
    
    if MM >= 60:
      MM -= 0
      HH += 1
     
    if HH >= 24:
      HH -= 24
      dd += 1
      
    if dd >= 30:
      dd -= 30
      mm += 1
    
    if mm >= 12:
      mm -= 12
      yyyy += 1
    
    datetime = '{:04d}{:02d}{:02d}{:02d}{:02d}{:02d}'.format(yyyy, mm, dd, HH, MM, SS)
    return int(datetime)