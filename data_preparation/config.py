WD = {
    'input': {
        'extract_raster': '/mnt/7E3B52AF2CE273C0/Thesis/backup_main_folder/Final-Thesis-Dataset/csv_files/',
        'prep_3draster' : './00_data_output/raster/'
    },
    'output': {
        'extract_raster': './00_data_output/raster/',
        'prep_3draster' : './00_data_output/3draster/'
    }
}

DATA_READ = {
  'name' : ['datetime', 'meshcode', 'rainfall', 'numsegments', 'congestion', 'accident', 'sns'],
  'idx'  : [1         , 2         , 5         , 6            , 9           , 15        , 13   ]
}

RASTER_CONFIG = {
    # factor map
    'width'             : 2000,
    'height'            : 2000,
    'offset_lat'        : 0.0020833333329974835,
    'offset_long'       : 0.003124999999982947,
    'start_lat'         : 33.588541666667005,
    'start_long'        : 134.10781250000002,
    'pixel_area'        : 0.25 ** 2, # 0.25km
    
    # factor channel index
    'congestion_channel'        : 0,
    'rainfall_channel'          : 1,
    'accident_channel'          : 2,
    'sns_channel'               : 3,

    'num_factors'               : 4
}

SEQUENCE = {
    'crop' : {
        'xS'    :   1402,
        'xE'    :   1502,
        'yS'    :   163,
        'yE'    :   413
    },

    'inp_len'    :   6, # 6 steps 
    'inp_delta'  :   1, # 12*5mins=1h
    'out_len'    :   3, # 3 steps
    'out_delta'  :   1, # 12*5mins=3h
    'out_factor' : RASTER_CONFIG['congestion_channel']
}

SNS_COMPLAINTS = ['交通', #accident/traffic
                  '台風,増水,雨,竜,浸水,地震', # rain
                  '渋滞,中止,渋滞,遅れ' # congestion
                 ]
                 
ACCIDENT_TYPES = ('0', '{v_to_m}', '{v_to_v_encounter}', '{v_to_v_front}', '{vehicle_own}',
                  '{v_to_v_left}', '{v_to_v_other}', '{v_to_v_rear}', '{v_to_v_right}')