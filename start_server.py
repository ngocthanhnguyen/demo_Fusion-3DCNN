import sys
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from data_preparation import TimeSeries2RasterImageConverter, SpatiotemporalRasterImageConverter
from data_preparation.data_utils import DataParser, DataReader, DataScaler
from data_preparation.jpmesh import *
from data_prediction import Fusion_3DCNN_CPA_SNS
import os
import time
app = Flask(__name__)

@app.route('/index')
def upload_file():
   return render_template('index.html')
	
@app.route('/result', methods = ['POST'])
def save_uploaded_file():
   if request.method == 'POST':
      f = request.files['file']
      savepath = './uploaded_files/' + secure_filename(f.filename)
      f.save(savepath)
      
      start_time = int(str(format_datetime(request.form.get('start_time'))))
      num_steps = int(request.form.get('num_steps'))
      offset_ref = int(request.form.get('offset_ref'))
      predicted_steps = int(request.form.get('predicted_steps'))
      offset_pred = int(request.form.get('offset_pred'))
      
      print('start_time={0}; num_steps={1}; offset_ref={2}; predicted_steps={3}; offset_pred={4}'\
            .format(start_time, num_steps, offset_ref, predicted_steps, offset_pred))
      
      calculate_predicted_time(start_time, offset_pred, num_steps, predicted_steps)
      
      start = time.time()      
      predict(savepath, start_time, num_steps, offset_ref)      
      stop = time.time()
      print('Execution time:',stop-start)
      return render_template('output.html')
      
# @app.route('/predicted/map_congested_<areaID>')
# def show_predictive_map(areaID):
  # return send_file('/predicted/map_congested_{0}.html'.format(areaID))
  
@app.route('/predicted/map_congested_0')
def map0():
    return render_template('/predicted/map_congested_0.html')
    
@app.route('/predicted/map_congested_1')
def map1():
    return render_template('/predicted/map_congested_1.html')
    
@app.route('/predicted/map_congested_2')
def map2():
    return render_template('/predicted/map_congested_2.html')
    
def format_datetime(datetime_input):
    for c in [':', '-', 'T']:
      datetime_input = datetime_input.replace(c, '')
      
    datetime_input += '00'
    return datetime_input
      
def predict(savepath, start_time, num_steps, offset_ref):
    tsConverter = TimeSeries2RasterImageConverter.TimeSeries2RasterImageConverter()
    print(savepath, start_time, num_steps, offset_ref)      
    tsConverter.convert([savepath], start_time, offset_ref ,num_steps)
    seqConverter = SpatiotemporalRasterImageConverter.SpatiotemporalRasterImageConverter()
    seqConverter.convert()
    
    print('Prediction')
    Fusion_3DCNN_CPA_SNS.load_and_predict()
    
    html_text = '<html><body>' + '\n'
    html_path = './templates/predicted/'
    map_files = os.listdir(html_path)
    map_files = sorted(map_files)
    i = 1
    for map_file in map_files:
      html_text += '<h1>Tình hình ùn tắc giao thông được dự đoán ở khu vực {0}</h1>'.format(i)
      i+=1
      #html_text += '<h1>{0}</h1>'.format(map_file)
      html_text += '<iframe style="display:block; width: 95%; height:100%;" src="{0}"'.format('/predicted/' + map_file.split('.')[0]) + '></iframe>' '\n'
      #html_text += '<p><a href="{0}" target="_blank"> {1} </a></p>\n'.format('/predicted/' + map_file.split('.')[0], map_file.split('.')[0])
      
    html_text += '</body></html>' + '\n'
    filehanlder = open('./templates/output.html', 'w')
    filehanlder.write(html_text)
    filehanlder.close()
    
@app.route("/getimage")
def get_img():
    return "a.jpg"
    
def calculate_predicted_time(start_time, offset, historical_steps, predicted_steps):
  for _ in range(historical_steps):
    start_time = determine_next_time(start_time, offset)    
  
  filehanlder = open('./00_data_output/predicted/time.csv', 'w')
  for i in range(predicted_steps):
    if i == 0:
      start_time = determine_next_time(start_time, 0)
    else:
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