from TimeSeries2RasterImageConverter import *
from SpatiotemporalRasterImageConverter import *

tsConverter = TimeSeries2RasterImageConverter()
tsConverter.convert(['20140503.csv'], 20140503002000, 40000 ,6)

seqConverter = SpatiotemporalRasterImageConverter()
seqConverter.convert()
