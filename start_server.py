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
      start = time.time()
      predict(savepath)
      stop = time.time()
      print('Execution time:',stop-start)
      return render_template('output.html')
      
@app.route('/predicted/map_congested_<areaID>')
def show_predictive_map(areaID):
  return render_template('/predicted/map_congested_{0}.html'.format(areaID))
      
def predict(savepath):
    tsConverter = TimeSeries2RasterImageConverter.TimeSeries2RasterImageConverter()
    tsConverter.convert([savepath], 20140503002000, 40000 ,6)
    seqConverter = SpatiotemporalRasterImageConverter.SpatiotemporalRasterImageConverter()
    seqConverter.convert()
    
    print('Prediction')
    Fusion_3DCNN_CPA_SNS.load_and_predict()
    
    html_text = '<html><body>' + '\n'
    html_path = './templates/predicted/'
    map_files = os.listdir(html_path)
    print(map_files)
    map_files = sorted(map_files)
    for map_file in map_files:
      # html_text += '<p><a href="{0}" target="_blank"> {1} </a></p>\n'.format(html_path + map_file, map_file.split('.')[0])
      html_text += '<p><a href="{0}" target="_blank"> {1} </a></p>\n'.format('/predicted/' + map_file.split('.')[0], map_file.split('.')[0])
      
    html_text += '</body></html>' + '\n'
    # print(html_text)
    filehanlder = open('./templates/output.html', 'w')
    filehanlder.write(html_text)
    filehanlder.close()
    
if __name__ == '__main__':
   app.run(debug = True)