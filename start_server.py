import sys
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from data_preparation import TimeSeries2RasterImageConverter, SpatiotemporalRasterImageConverter
from data_preparation.data_utils import DataParser, DataReader, DataScaler
from data_preparation.jpmesh import *
from data_prediction import Fusion_3DCNN_CPA_SNS
import os
import time
app = Flask(__name__)

@app.route('/upload')
def upload_file():
   return render_template('upload.html')
	
@app.route('/uploader', methods = ['POST'])
def save_uploaded_file():
   if request.method == 'POST':
      f = request.files['file']
      savepath = './uploaded_files/' + secure_filename(f.filename)
      f.save(savepath)
      
      start_time = int(request.form.get('start_time'))
      num_steps = int(request.form.get('num_steps'))
      offset = int(request.form.get('offset'))
      predicted_steps = int(request.form.get('predicted_steps'))
      calculate_predicted_time(start_time, offset, num_steps, predicted_steps)
      
      start = time.time()
      predict(savepath, start_time, num_steps, offset)      
      stop = time.time()
      print('Execution time:',stop-start)
      return render_template('output.html')
      
@app.route('/predicted/map_congested_<areaID>')
def show_predictive_map(areaID):
  return render_template('/predicted/map_congested_{0}.html'.format(areaID))
      
def predict(savepath, start_time, num_steps, offset):
    tsConverter = TimeSeries2RasterImageConverter.TimeSeries2RasterImageConverter()
    tsConverter.convert([savepath], start_time, offset ,num_steps)
    seqConverter = SpatiotemporalRasterImageConverter.SpatiotemporalRasterImageConverter()
    seqConverter.convert()
    
    print('Prediction')
    Fusion_3DCNN_CPA_SNS.load_and_predict()
    
    html_text = '<html><body>' + '\n'
    html_path = './templates/predicted/'
    map_files = os.listdir(html_path)
    map_files = sorted(map_files)
    for map_file in map_files:
      html_text += '<p><a href="{0}" target="_blank"> {1} </a></p>\n'.format('/predicted/' + map_file.split('.')[0], map_file.split('.')[0])
      
    html_text += '</body></html>' + '\n'
    filehanlder = open('./templates/output.html', 'w')
    filehanlder.write(html_text)
    filehanlder.close()
    
def calculate_predicted_time(start_time, offset, historical_steps, predicted_steps):
  for _ in range(historical_steps):
    start_time = determine_next_time(start_time, offset)    
  
  filehanlder = open('./00_data_output/predicted/time.csv', 'w')
  for _ in range(predicted_steps):
    start_time = determine_next_time(start_time, offset)
    time_str = str(start_time)
    time_str = time_str[0:4] + '-' + time_str[4:6] + '-' + time_str[6:8] + ' ' + time_str[8:10] + ':' + time_str[10:12] + ':' + time_str[12:14]
    filehanlder.write(time_str + '\n')   
    
  filehanlder.close()
  
  
def determine_next_time(curr_time, offset):
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
    
if __name__ == '__main__':
   app.run(debug = True)