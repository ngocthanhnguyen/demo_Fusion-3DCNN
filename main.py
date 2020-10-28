# from config import *
from data_preparation import TimeSeries2RasterImageConverter, SpatiotemporalRasterImageConverter
from data_preparation.data_utils import DataParser, DataReader, DataScaler
from data_preparation.jpmesh import *
from data_prediction import Fusion_3DCNN_CPA_SNS
import os

def main():
  # print('TimeSeries2RasterImageConverter')
  tsConverter = TimeSeries2RasterImageConverter.TimeSeries2RasterImageConverter()
  tsConverter.convert(['./data_preparation/20140503.csv'], 20140503002000, 40000 ,6)

  # print('SpatiotemporalRasterImageConverter')
  seqConverter = SpatiotemporalRasterImageConverter.SpatiotemporalRasterImageConverter()
  seqConverter.convert()
  
  # print('Prediction')
  Fusion_3DCNN_CPA_SNS.load_and_predict()
  
  html_text = '<html><body>' + '\n'
  html_path = './00_data_output/predicted/'
  map_files = os.listdir(html_path)
  map_files = sorted(map_files)
  for map_file in map_files:
    html_text += '<p><a href="{0}" target="_blank"> {1} </a></p>\n'.format(html_path + map_file, map_file.split('.')[0])
    
  html_text += '</body></html>' + '\n'
  
  filehandler = open('final.html', 'w')
  filehandler.write(html_text)
  filehandler.close()

main()