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

from django.core.files.storage import default_storage
from django.conf import settings

from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status

from .serializers import UploadImageSerializer, TrainModelSerializer

from classifier import services as classifierService

IMAGE_SIZE = (128, 128)


class UploadImageView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        """Handle multiple image uploads and store in database"""
        class_name = request.data.get("class_name")
        files = request.FILES.getlist("images")  # Get multiple files

        if not class_name or not files:
            return Response({"error": "Class name and images are required"}, status=status.HTTP_400_BAD_REQUEST)

        result = UploadImageSerializer.save_multiple(files, class_name)  # Call save_multiple method
        
        if isinstance(result, dict) and "error" in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        # return Response({"message": "Images uploaded successfully!"}, status=status.HTTP_201_CREATED)
        return Response({"message": "Images uploaded successfully!", "images": [str(img) for img in result]}, status=status.HTTP_201_CREATED)

class TrainModelView(generics.GenericAPIView):
    serializer_class = TrainModelSerializer
    def get(self, request):
        classifierService.start_training_process()
        response = { "message": "The Image Classifier Model was trained successfully!" }
        return Response(response, status=status.HTTP_200_OK)
    
# class PredictImageView(APIView):
#     def post(self, request):
#         """Classify an image using the trained model"""
#         uploaded_image = request.FILES['image']
#         image_path = default_storage.save('temp/' + uploaded_image.name, uploaded_image)

#         model = classifierService.load_trained_model()
#         class_names = classifierService.load_class_names()
        
#         image = cv2.imread(image_path)
#         image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#         image_resized = cv2.resize(image, IMAGE_SIZE) / 255.0

#         # image_array = np.expand_dims(image_resized, axis=0)
#         # prediction = model.predict(image_array)
#         # predicted_class = list(class_names.keys())[np.argmax(prediction)]

#         return Response({"predicted_class": image}, status=status.HTTP_200_OK)

class PredictImageView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        """Classify an image using the trained model"""
        if 'image' not in request.FILES:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_image = request.FILES['image']
        image_path = default_storage.save('temp/uploads/' + uploaded_image.name, uploaded_image)  # Save temp image

        try:
            # Load and preprocess the image
            image = cv2.imread(os.path.join(settings.MEDIA_ROOT, image_path))
            # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert from BGR to RGB
            image_resized = cv2.resize(image, IMAGE_SIZE) / 255.0  # Resize and normalize

            # Load the trained model
            model = classifierService.load_trained_model()

            # Predict
            image_array = np.expand_dims(image_resized, axis=0)  # Expand dimensions for model input
            prediction = model.predict(image_array)
            predicted_class_index = np.argmax(prediction)

            # Retrieve class names from dataset
            dataset_dir = os.path.join(settings.MEDIA_ROOT, "dataset")
            class_names = sorted(os.listdir(dataset_dir)) # Ensure sorted order

            predicted_class = class_names[predicted_class_index] if predicted_class_index < len(class_names) else "Unknown"

            return Response({"predicted_class": predicted_class}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            # Cleanup temp file
            if os.path.exists(os.path.join(settings.MEDIA_ROOT, image_path)):
                os.remove(os.path.join(settings.MEDIA_ROOT, image_path))