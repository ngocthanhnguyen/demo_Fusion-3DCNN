import sys
sys.path.append('../')
from data_preparation import *
from data_prediction import *
from flask import Flask
app = Flask(__name__)


@app.route("/")
def home():
    print('calling main')
    data_preparation.main()
    print('after main')
    return "<h1>Not Much Going On Here</h1>"


app.run(host='0.0.0.0', port=60000)
