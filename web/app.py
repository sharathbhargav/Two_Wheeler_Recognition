from flask import Flask, jsonify, render_template, flash, request, redirect, url_for,url_for, send_from_directory
from werkzeug.utils import secure_filename
import os

import base64
from fastai.vision import load_learner,open_image
app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MODEL_PATH']='static/models'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class InvalidImageException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

def save_image(request):
    if 'file' not in request.files:
            #flash('No file part')
        print("No file part")
        raise InvalidImageException("No file part")
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        #flash('No selected file')
        raise InvalidImageException("Invalid file name")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print(filename)
        return filename

@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'POST':
        # check if the post request has the file part
        try:
            filename = save_image(request)
            return redirect(url_for('uploaded_file',filename=filename))
        except InvalidImageException :
            
            return render_template(request.url)
            
    print("index")
    return render_template('index.html')

  

def get_predictions(filename):
    model = load_learner(app.config['MODEL_PATH'],file='exportV1.pkl')
    img = open_image(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    pred_class,idx,outputs = model.predict(img)
    mapped=sorted(set(zip(outputs, model.data.classes)),reverse=True)

    #os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return {'class':str(pred_class),'detail':str(mapped)}


@app.route('/v1/results/<filename>',methods=['GET'])
def uploaded_file(filename):
    if request.method == "GET":
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            output = get_predictions(filename)
            return render_template('uploaded_file.html',filename=filename,pred_class=output['class'])

@app.route('/v1/results',methods=['POST'])
def image_api():
    print("iamge api")
    if request.method == "POST":
        try:
            filename = save_image(request)
            results = get_predictions(filename)
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            print((jsonify(results)))
            return jsonify( results)
        except InvalidImageException as e:
            print(e.message)
            return jsonify({"error":e.message})


@app.route('/clean_up/<filename>')
def clean_up(filename):
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host= '0.0.0.0',debug=True,port='5000')