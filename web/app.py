import keras
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file

# Packages for SVM
import cv2  # for reading image in SVM
import joblib  # for loading model in SVM

# packages for CNN
import tensorflow as tf
from keras.preprocessing import image  # for image preprocessing in CNN

# import the necessary packages for histogram equalization
from matplotlib import pyplot as plt
from skimage import feature
import numpy as np

# other packages
import os
from werkzeug.utils import secure_filename


class LocalBinaryPatterns:
    def __init__(self, numPoints, radius):
        # store the number of points and radius
        self.numPoints = numPoints
        self.radius = radius

    def describe(self, image_local, eps=1e-7):
        # compute the Local Binary Pattern representation
        # of the image, and then use the LBP representation
        # to build the histogram of patterns

        lbp = feature.local_binary_pattern(image_local, self.numPoints, self.radius, method="uniform")
        (hist, _) = np.histogram(lbp.ravel(), bins=np.arange(0, self.numPoints + 3), range=(0, self.numPoints + 2))

        # normalize the histogram
        hist = hist.astype("float")
        hist /= (hist.sum() + eps)

        # return the histogram of Local Binary Patterns
        return hist


UPLOAD_FOLDER = 'web\\static\\uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["CACHE_TYPE"] = "null"


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        f = request.files['file']
        # save the file to the uploads folder
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        # save the path of the image
        image_path = os.path.join(UPLOAD_FOLDER, f.filename)

        # If the Selected option was SVM
        if request.form['algo-sel'] == 'svm':
            gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # read the imgage
            data = LocalBinaryPatterns(24, 8).describe(gray)  # get the LBP histogram
            model = joblib.load('model\\SVM_rbf.h5')  # load the model
            return render_template('index.html', modelName="SVM", result=model.predict(data.reshape(1, -1))[0],
                                   filename=f.filename)

        # If the Selected option was CNN
        else:
            model = tf.keras.models.load_model('model/CNN_classification.h5')  # load the model
            test_image = image.load_img(image_path, target_size=(128, 128))  # load the image
            test_image = image.img_to_array(test_image)  # converting image to array
            test_image = np.expand_dims(test_image, axis=0)  # expanding shape of an array
            result = model.predict(test_image)  # giving test_image array to model for prediction
            prediction = ''
            if result[0][0] == 1:
                prediction = 'Live'
            else:
                prediction = 'Fake'
            return render_template('index.html', modelName="CNN", result=prediction, filename=f.filename)
    else:  # if the request is GET then simply render the index.html
        return render_template('index.html')


@app.route('/matching', methods=['POST', 'GET'])
def matching():
    if request.method == 'POST':
        return render_template('mathching', )
    else:
        return render_template('matching.html')


@app.route('/reconstruction', methods=['POST', 'GET'])
def reconstruction():
    if request.method == 'POST':
        f = request.files['file']
        # save the file to the uploads folder
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        # save the path of the image
        image_path = os.path.join(UPLOAD_FOLDER, f.filename)

        autoencoder = keras.models.load_model('model/Reconstructing.h5')
        test_image = tf.keras.utils.load_img(image_path, target_size=(224, 224))
        images_arr1 = np.asarray(test_image)
        images_arr1 = images_arr1.astype('float32')
        # images_arr1.shape
        images_arr1 = images_arr1[..., 0]

        images_arr1 = images_arr1.reshape(-1, 224, 224, 1)
        images_arr1 = images_arr1 / np.max(images_arr1)
        images_arr1 = images_arr1.reshape(-1, 224, 224, 1)
        pred1 = autoencoder.predict(images_arr1)
        fig = plt.figure(figsize=(20, 4))
        fig.add_subplot(1, 2, 1)
        print("Showing Test Images")
        for i in range(1):
            plt.imshow(images_arr1[i, ..., 0], cmap='gray')
            plt.title("Original Image" + str(f.filename))
            print(f.filename)
        fig.add_subplot(1, 2, 2)
        print("Reconstruction of Test Images")
        for i in range(1):
            plt.imshow(pred1[i, ..., 0], cmap='gray')
            plt.title("Reconstructed Image")
        save_str = "web/static/uploads/reconstructed.png"
        if os.path.exists(save_str):
            os.remove(save_str)
        plt.savefig(save_str, bbox_inches='tight')
        plt.close()
        return render_template('reconstruction.html', filename='reconstructed.png', result="Done with reconstruction successfully")
    return render_template('reconstruction.html')


# To see the image that user has recently uploaded
@app.route('/get_image/<filename>')
def get_image(filename):
    try:
        return_string = 'static/uploads/' + filename
        return send_file(return_string, attachment_filename=filename)
    except Exception as e:
        return str(e)


if __name__ == '__main__':
    app.run(debug=True, port=3000)
