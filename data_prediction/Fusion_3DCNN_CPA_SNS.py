import numpy as np
import os, fnmatch
import matplotlib.pyplot as plt
from keras import *
from .data_config import *
import seaborn as sns
from .util import *

import os
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"   # see issue #152
os.environ["CUDA_VISIBLE_DEVICES"] = ""

#######################
## Configure dataset ##
#######################
dataset_path = '/mnt/7E3B52AF2CE273C0/Thesis/dataset/dataset/s6_4h_s6_4h'
WD = {
    'input': {
      'model_weights' : {
        '6_40000_6_40000': '/mnt/d/00_Backup_Thesis/00_defence/train_mdls_Fusion-3DCNN/6steps_4hours_6steps_4hours/Fusion-3DCNN_CPA_SNS_075/epoch_15000.h5',
        '6_6000_3_6000': '/mnt/d/00_Backup_Thesis/00_defence/train_mdls_Fusion-3DCNN/6steps_1hour_3steps_1hour/Fusion-3DCNN_CPA_SNS_075/epoch_15000.h5',
        '6_3000_3_3000': '/mnt/d/00_Backup_Thesis/00_defence/train_mdls_Fusion-3DCNN/6steps_30mins_3steps_30mins/Fusion-3DCNN_CPA_SNS_025/epoch_15000.h5'
      },
      'datetime_data' : './00_data_output/raster/datetime_data.csv'
    },    
    'output' : {
      'predictive_map' : './templates/predicted/'
    }
}

REDUCE_DIMENSION = False
REDUCED_WEIGHT = 0.75
DATA_FILE = './00_data_output/3draster/hist_data.npz'
VISUALIZATION_TYPE = 'folium' # option: ['sns', 'folium']

###########################################
## Load data for training and evaluating ##
###########################################
# Load training data
def loadDataFile(path, areaId, mode):
    try:
        data = np.load(path)
        data = data['arr_0']
    except Exception:
        data = None  
    if mode == 'X'  :
        mask = np.zeros(GLOBAL_SIZE_X)
    else:
        mask = np.zeros(GLOBAL_SIZE_Y)
    data = data[:, BOUNDARY_AREA[areaId][0]:BOUNDARY_AREA[areaId][1], BOUNDARY_AREA[areaId][2]:BOUNDARY_AREA[areaId][3], :]
    mask[:, PADDING[areaId][0]:PADDING[areaId][1], PADDING[areaId][2]:PADDING[areaId][3], :] = data
    
    return mask
    
def fuseFactors(factorName, factorData):
    main_factor = factorData[:, :, :, FACTOR[factorName]]
    main_factor = np.expand_dims(main_factor, axis=3)
    main_factor = np.expand_dims(main_factor, axis=0)
    main_factor = main_factor.astype(float)
    main_factor /= MAX_FACTOR[factorName]

    if factorName == 'Input_accident':
        main_factor[main_factor > 0] = 1

    if factorName != 'default' and factorName != 'Input_sns':
        secondary_factor = factorData[:, :, :, FACTOR['Input_sns']]
        secondary_factor = np.expand_dims(secondary_factor, axis=3)
        secondary_factor = np.expand_dims(secondary_factor, axis=0)        
        secondary_factor = secondary_factor.astype(int)

        for idx in LINK_FACTOR[factorName]:
            main_factor[secondary_factor == idx] = (1-REDUCED_WEIGHT) * main_factor[secondary_factor == idx]
    
    return main_factor

def appendFactorData(factorName, factorData, X):
    data = fuseFactors(factorName, factorData)

    if X[factorName] is None:
        X[factorName] = data
    else:
        X[factorName] = np.vstack((X[factorName], data))

    return X

def loadData(dataFile, areaId):
    # Initialize data
    X = {}
    for key in FACTOR.keys():
        X[key] = None
    
    # Load factors and predicted data
    seqName = dataFile    
    factorData = loadDataFile(dataFile, areaId, 'X')

    for key in FACTOR.keys():
        X = appendFactorData(key, factorData, X)
    
    return X

##########################
## Build learning model ##
##########################
def buildCNN(cnnInputs, imgShape, filters, kernelSize, factorName, isFusion=False, cnnOutputs=None):
    if isFusion == True:
        cnnInput = layers.add(cnnOutputs, name='Fusion_{0}'.format(factorName))
    else:
        cnnInput = layers.Input(shape=imgShape, name='Input_{0}'.format(factorName))

    for i in range(len(filters)):
        counter = i+1
        if i == 0:
            cnnOutput = cnnInput

        cnnOutput = layers.Conv3D(filters=filters[i], kernel_size=kernelSize, strides=1, padding='same', activation='tanh',
                                  name='Conv3D_{0}{1}'.format(factorName, counter))(cnnOutput)
        cnnOutput = layers.BatchNormalization(name='BN_{0}{1}'.format(factorName, counter))(cnnOutput)
    
    if cnnInputs is not None:
        cnnModel = Model(inputs=cnnInputs, outputs=cnnOutput)
    else:
        cnnModel = Model(inputs=cnnInput, outputs=cnnOutput)
    return cnnModel
    
def buildPrediction(orgInputs, filters, kernelSize, lastOutputs=None):
    global REDUCE_DIMENSION
    predictionOutput = None
    for i in range(len(filters)):
        counter = i + 1
        if i == 0:
            if lastOutputs is not None:
                predictionOutput = lastOutputs
            else:
                predictionOutput = orgInputs
                    
        predictionOutput = layers.Conv3D(filters=filters[i], kernel_size=kernelSize, strides=1, padding='same', activation='sigmoid', 
                                         name='Conv3D_prediction{0}1'.format(counter))(predictionOutput)        
        predictionOutput = layers.Conv3D(filters=filters[i], kernel_size=kernelSize, strides=1, padding='same', activation='relu', 
                                         name='Conv3D_prediction{0}2'.format(counter))(predictionOutput)
    
    if REDUCE_DIMENSION == True:
        predictionOutput = layers.MaxPooling3D(pool_size=(2,1,1), name='output')(predictionOutput)

    predictionOutput = Model(inputs=orgInputs, outputs=predictionOutput)
    return predictionOutput

def buildCompleteModel(imgShape, filtersDict, kernelSizeDict):
    # Define architecture for learning individual factors
    filters = filtersDict['factors']
    kernelSize= kernelSizeDict['factors']
    
    congestionCNNModel   = buildCNN(cnnInputs=None, imgShape=imgShape, filters=filters, kernelSize=kernelSize, factorName='congestion')
    rainfallCNNModel     = buildCNN(cnnInputs=None, imgShape=imgShape, filters=filters, kernelSize=kernelSize, factorName='rainfall')
    accidentCNNModel     = buildCNN(cnnInputs=None, imgShape=imgShape, filters=filters, kernelSize=kernelSize, factorName='accident')

    # Define architecture for fused layers
    filters = filtersDict['factors_fusion']
    kernelSize= kernelSizeDict['factors_fusion']

    fusedCNNModel       = buildCNN(cnnInputs=[congestionCNNModel.input, rainfallCNNModel.input, accidentCNNModel.input],
                                   cnnOutputs=[congestionCNNModel.output, rainfallCNNModel.output, accidentCNNModel.output],
                                   imgShape=imgShape,
                                   filters=filters, kernelSize=kernelSize,
                                   factorName='factors', isFusion=True
                                  )

    # Define architecture for prediction layer
    filters = filtersDict['prediction']
    kernelSize= kernelSizeDict['prediction']
    predictionModel     = buildPrediction(orgInputs=[congestionCNNModel.input, rainfallCNNModel.input, accidentCNNModel.input],
                                          filters=filters,
                                          kernelSize=kernelSize,
                                          lastOutputs=fusedCNNModel.output
                                         )            

    return predictionModel

def select_trained_data(num_steps, offset_ref, predicted_steps, offset_pred):
  global REDUCE_DIMENSION
  data_check = str(num_steps) + '_' + str(offset_ref) + '_' + str(predicted_steps) + '_' + str(offset_pred)
  trained_data_file = WD['input']['model_weights'][data_check]
  if predicted_steps == num_steps//2:    
    REDUCE_DIMENSION = True
  return trained_data_file
  
def load_and_predict(num_steps, offset_ref, predicted_steps, offset_pred):
  trained_data_file = select_trained_data(num_steps, offset_ref, predicted_steps, offset_pred)
  print('select_trained_data:', num_steps, offset_ref, predicted_steps, offset_pred, trained_data_file)
  imgShape = (6,60,80,1)
  filtersDict = {}; filtersDict['factors'] = [128, 128, 256]; filtersDict['factors_fusion'] = [256, 256, 256, 128]; filtersDict['prediction'] = [64, 1]
  kernelSizeDict = {}; kernelSizeDict['factors'] = (3,3,3); kernelSizeDict['factors_fusion'] = (3,3,3); kernelSizeDict['prediction'] = (3,3,3)

  predictionModel = buildCompleteModel(imgShape, filtersDict, kernelSizeDict)
  predictionModel.load_weights(trained_data_file)
  # predictionModel.summary()

  for areaId in range(len(BOUNDARY_AREA)):
    print(DATA_FILE, areaId)
    # load and predict
    data = loadData(DATA_FILE, areaId)
    predicted = predictionModel.predict(data)
    predicted = predicted[0] * MAX_FACTOR['Input_congestion']
    
    print_historical_statistics(data)
    
    export_predictive_map_folium(predicted, areaId, WD['output']['predictive_map'])