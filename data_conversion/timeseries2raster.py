## Importing the libraries
import numpy as np
import os
from config import *
import sys
# sys.path.append('./')
from data_utils.DataParser import *
from data_utils.DataReader import *
from data_utils.DataScaler import *
from jpmesh.jpmesh import *

class TimeSeries2RasterImageConverter:
    def __init__(self, data_file):        
        self.dp = DataParser()
        self.ds = DataScaler()

        if 1 == 0:
            # ============================================ #
            # Needed columns for extraction
            col_name = ['datetime', 'meshcode', 'rainfall', 'numsegments', 'congestion', 'accident', 'sns']
            col_idx  = [1         , 2         , 5         , 6            , 9           , 15        , 13]
            target_col = len(col_name) - 1

            # ============================================ #
            # Data location
            data_path = WD['input']['extract_raster']           # path to time series dataset
            output_raster_path = WD['output']['extract_raster'] # path to raster image storage

            # ============================================ #
            # Read data
            data_files = os.listdir(data_path)
            data_files.sort()
            for i in range(len(data_files)):
                data_files[i] = data_path + data_files[i]
            
            dr = DataReader(data_files, col_idx)
            ds = DataScaler()
            dp = DataParser()

            needed_col_name = col_name[:-1]
            needed_col_name.append('latitude')
            needed_col_name.append('longitude')

            if len(sys.argv) > 2:
                start = int(sys.argv[1])
                end = int(sys.argv[2])
            else:
                start = data_files.index('./csv_files/20140916.csv')
                end = data_files.index('./csv_files/20141031.csv')

            for file_id in range(start, end):
                #if '2015' not in data_files[file_id]:
                #    continue
                dr_tmp = DataReader([data_files[file_id]], col_idx)
                dr_tmp.read(delimiter='\t')
                data = dr_tmp.getData()
                data = parse_data(dp, data, col_name, target_col)
                
                generate_factor_map(output_raster_path, data, needed_col_name, RASTER_CONFIG)
                del data
                del dr_tmp

    def convert(self, data_file, start_time, steps):
        # read data from csv
        self.dr = DataReader(data_file, DATA_READ['idex'])
        dr.read(delimiter='\t')
        data = getData()

        # parse data
        data = parse_data(data)

        # generate raster
        raster = self.generate_factor_map()

    def parse_data(self, data):
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

        # meshcode to coordination
        data = self.dp.removeDelimiters(data, DATA_READ['name'].index('center'), ('POINT(', ')'))    
        data = self.dp.convertLocation(data, DATA_READ['name'].index('center'), ' ')
        
        return data

    def generate_factor_map(self, data):
        loc = {}

        date = data[0, DATA_READ['name'].index('datetime')]
        date //= 1000000

        timecode = 0
        j = 0

        timecodesPerDay = 288

        while timecode < timecodesPerDay:
            time = convert_idx2time(timecode)
            starting_time = str(date) + time
            factor_map = np.zeros((RASTER_CONFIG['width'], RASTER_CONFIG['height'],RASTER_CONFIG['num_factors']))
            
            while j < data.shape[0]:
                ending_time = data[j, DATA_READ['name'].index('datetime')] // 100
                if str(ending_time) > starting_time:
                    break

                # get center coordination of each mesh
                meshcode = data[j, DATA_READ['name'].index('meshcode')]
                mesh = parse_mesh_code(str(meshcode))
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

                j += 1

            factor_map = np.flip(factor_map, axis=0)

            dump_factor(WD['output']['extract_raster'] + starting_time, factor_map)
            del factor_map

            timecode += 1




def convert_idx2time(id, step=5):
    hh = mm = ss = 0
    step_per_min = int(60/step)

    if id < step_per_min:
        mm = id * step
    else:
        hh = id // step_per_min
        mm = id % step_per_min * 5
    
    time = '{:02d}{:02d}'.format(hh, mm)
    return time

def dump_factor(path, factor_map):
    np.savez_compressed(path, factor_map)



if __name__ == "__main__":
    # ============================================ #
    # Needed columns for extraction
    col_name = ['datetime', 'meshcode', 'rainfall', 'numsegments', 'congestion', 'accident', 'sns']
    col_idx  = [1         , 2         , 5         , 6            , 9           , 15        , 13]
    target_col = len(col_name) - 1

    # ============================================ #
    # Data location
    data_path = WD['input']['extract_raster']           # path to time series dataset
    output_raster_path = WD['output']['extract_raster'] # path to raster image storage

    # ============================================ #
    # Read data
    data_files = os.listdir(data_path)
    data_files.sort()
    for i in range(len(data_files)):
        data_files[i] = data_path + data_files[i]
    
    dr = DataReader(data_files, col_idx)
    ds = DataScaler()
    dp = DataParser()

    needed_col_name = col_name[:-1]
    needed_col_name.append('latitude')
    needed_col_name.append('longitude')

    if len(sys.argv) > 2:
        start = int(sys.argv[1])
        end = int(sys.argv[2])
    else:
        start = data_files.index('./csv_files/20140916.csv')
        end = data_files.index('./csv_files/20141031.csv')

    for file_id in range(start, end):
        #if '2015' not in data_files[file_id]:
        #    continue
        dr_tmp = DataReader([data_files[file_id]], col_idx)
        dr_tmp.read(delimiter='\t')
        data = dr_tmp.getData()
        data = parse_data(dp, data, col_name, target_col)
        
        generate_factor_map(output_raster_path, data, needed_col_name, RASTER_CONFIG)
        del data
        del dr_tmp
    
