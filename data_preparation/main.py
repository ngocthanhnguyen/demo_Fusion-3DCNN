from TimeSeries2RasterImageConverter import *
from SpatiotemporalRasterImageConverter import *

def main():
  print('TimeSeries2RasterImageConverter')
  tsConverter = TimeSeries2RasterImageConverter()
  tsConverter.convert(['20140503.csv'], 20140503002000, 40000 ,6)

  print('SpatiotemporalRasterImageConverter')
  seqConverter = SpatiotemporalRasterImageConverter()
  seqConverter.convert()

main()