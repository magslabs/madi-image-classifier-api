from rest_framework import serializers
from .models import UploadImage

class UploadImageSerializer(serializers.ModelSerializer): 
    class Meta:
        model = UploadImage
        fields = '__all__'
        
    @classmethod
    def save_multiple(cls, files, class_name):
        """Handles bulk image uploads"""
        instances = []
        for file in files:
            serializer = cls(data={'class_name': class_name, 'image': file})
            if serializer.is_valid():
                instances.append(serializer.save())  # Save validated data
            else:
                return {"error": serializer.errors}  # Return validation errors
        
        return instances  # Return the list of saved images
        
class TrainModelSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=256)