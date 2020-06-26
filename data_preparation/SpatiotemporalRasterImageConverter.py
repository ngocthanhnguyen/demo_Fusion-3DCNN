import numpy as np
import os
import fnmatch
from .config import *

class SpatiotemporalRasterImageConverter:
  def __init__(self):
    pass
    
  def _load_raster(self, path):
    iCorrupted = False
    factorsMap = None

    try:
        factorsMap = np.load(path)
        factorsMap = factorsMap['arr_0']
    except Exception:
        # sometime, a npz file gets corrupted
        iCorrupted = True

    return iCorrupted, factorsMap
    
  def _crop_raster(self, data):
    data = data[SEQUENCE['crop']['xS'] : SEQUENCE['crop']['xE'], SEQUENCE['crop']['yS'] : SEQUENCE['crop']['yE'], :]
    return data
      
  def _dump_data(self, path, seq_raster):
    np.savez_compressed(path, seq_raster)
  
  def convert(self, delete=True):
    input_files = fnmatch.filter(os.listdir(WD['input']['prep_3draster']), '*.npz')
    input_files.sort() 
    
    seq_raster = None
    for input_file in input_files:
      iCorrupted, raster_img = self._load_raster(WD['input']['prep_3draster'] + input_file)
      if iCorrupted:
        raise Exception('Corrupted data file', input_file)
        
      raster_img = self._crop_raster(raster_img)
      
      raster_img = np.expand_dims(raster_img, axis=0)
      if seq_raster is None:
        seq_raster = raster_img
      else:
        seq_raster = np.vstack((seq_raster, raster_img))
    
      
      os.remove(WD['input']['prep_3draster'] + input_file)
    
    print(seq_raster.shape)
    self._dump_data(WD['output']['prep_3draster'] + 'hist_data', seq_raster)
    
