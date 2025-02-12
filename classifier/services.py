import tensorflow as tf
import lz4
import os, random, time
import cv2
import numpy as np
from tensorflow.keras import layers, models
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
from numpy import asarray
from PIL import Image
from matplotlib import pyplot
from matplotlib.patches import Rectangle, Circle
from mtcnn.mtcnn import MTCNN

# from .models import UploadImage
from django.conf import settings

images_dir = os.path.join(settings.MEDIA_ROOT, 'dataset') # dataset directory
staticfiles_dir = settings.STATIC_ROOT

# Ensure the static folder exists
os.makedirs(staticfiles_dir, exist_ok=True)

image_data = []
labels = [] 
class_names = os.listdir(images_dir)

x_train = []
x_val = 0
y_train = []
x_val = 0

image_data_np = []
labels_np = []

def load_trained_model():
    model_path = os.path.join(staticfiles_dir, "classifier_model.keras")
    if os.path.exists(model_path):
        return load_model(model_path)
    else:
        raise FileNotFoundError("Model file 'classifier_model.keras' not found. Please train the classifier first.")
    
def load_class_names():
    return class_names

def draw_image_with_boxes(filename, result_list):
    # Load the image
    data = pyplot.imread(filename)
    # Plot the image
    pyplot.imshow(data)
    # Get the context for drawing boxes
    ax = pyplot.gca()
    # Plot each box
    for result in result_list:
        # Get coordinates
        x, y, width, height = result['box']
        # Create the shape
        rect = Rectangle((x, y), width, height, fill=False, color='red')
        # Draw the box
        ax.add_patch(rect)
        # Draw the dots
        for key, value in result['keypoints'].items():
            # Create and draw a circle
            dot = Circle(value, radius=2, color='red')
            ax.add_patch(dot)
            
    # Show the plot
    # pyplot.show()

def extract_face_from_image(image_path, required_size=(128, 128)):
    # load image and detect faces
    image = pyplot.imread(image_path)
    detector = MTCNN()
    faces = detector.detect_faces(image)

    face_images = []

    for face in faces:
        # extract the bounding box from the requested face
        x1, y1, width, height = face['box']
        x2, y2 = x1 + width, y1 + height

        # extract the face
        face_boundary = image[y1:y2, x1:x2]

        # resize pixels to the model size
        face_image = Image.fromarray(face_boundary)
        face_image = face_image.resize(required_size)
        face_array = asarray(face_image)
        face_images.append(face_array)

    return face_images

def load_dataset(data_dir=images_dir):
    global image_data, labels
    print("Loading dataset...")
    image_data, labels = [], []

    for idx, class_name in enumerate(class_names):
        class_dir = os.path.join(data_dir, class_name)
        for img_file in os.listdir(class_dir):
            img_path = os.path.join(class_dir, img_file)
            # load image from file
            pixels = pyplot.imread(img_path)
            # create the detector, using default weights
            detector = MTCNN()
            # detect faces in the image
            faces = detector.detect_faces(pixels)

            #check if any faces were detected
            if len(faces) > 0:
              # display faces on the original image
              draw_image_with_boxes(img_path, faces)
              extracted_face = extract_face_from_image(img_path)

              img_array = tf.keras.utils.img_to_array(cv2.resize(extracted_face[0],(128,128))) #get the first image. previously just img
              image_data.append(img_array)
              labels.append(idx)
            else:
              print(f"No faces detected in {img_path}, skipping...")

    image_data = tf.convert_to_tensor(image_data) / 255.0  # Normalize images

    labels = tf.convert_to_tensor(labels)
    
    print("Dataset loaded successfully.")
    
def build_model():
    print("Building model...")
    global x_train, x_val, y_train, y_val, image_data_np, labels_np
    
    image_data_np = image_data.numpy()
    labels_np = labels.numpy()
    
    x_train, x_val, y_train, y_val = train_test_split(image_data_np, labels_np, test_size=0.2, random_state=42)
    model = models.Sequential([
        layers.Conv2D(32, (3, 3), activation='relu', input_shape=(128, 128, 3)),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dense(len(class_names), activation='softmax')
    ])
    
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

def train_model():
    print("Training model...")
    model = build_model()
    model_path = os.path.join(staticfiles_dir, "classifier_model.keras")
    if os.path.exists(model_path):
        model = load_model(model_path)
        model.fit(
            x_train, y_train, 
            validation_data=(x_val, y_val),
            epochs=20, batch_size=8, verbose=1)
        model.save(os.path.join(staticfiles_dir, "classifier_model.keras"))
    else:
        model = build_model()
        model.fit(
            x_train, y_train, 
            validation_data=(x_val, y_val),
            epochs=10, batch_size=8, verbose=1)
        model.save(os.path.join(staticfiles_dir, "classifier_model.keras"))    
    
    print("Model trained successfully.")
    evaluate_model(model)
    
def evaluate_model(model):
    print("Evaluating model...")
    val_loss, val_accuracy = model.evaluate(image_data, labels)
    print(f"Validation Accuracy: {val_accuracy:.2f}")
    print(f"Validation Loss: {val_loss:.2f}")
        
    if val_accuracy < 0.8:
        print("Model accuracy is below 80%. Retraining...")
        train_model()
    else:
        print("Model accuracy is above 80%. Model training complete.")
        
def start_training_process():
    load_dataset()
    train_model()

