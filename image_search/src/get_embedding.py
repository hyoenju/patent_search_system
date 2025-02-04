from image_search.src.autoencoder import model
import os
from keras.layers import Input
from keras.models import Model
import keras.backend.tensorflow_backend as K
from image_search.src.load_images import readImg


def get_embedding(image_file, model_path='best_model.h5', image_shape=(64, 64)):
    with K.tf.device('/cpu:0'):
        input_image = Input(shape=image_shape+(1,))
        c_ae = model(None, input_image)
        c_ae.load_weights(os.path.join(os.getcwd(), model_path))
        embd_model = Model(inputs=c_ae.input,
                           outputs=c_ae.get_layer('embeddings').output)
        img = readImg(image_file)
        embd_value = embd_model.predict(img)
    return embd_value
