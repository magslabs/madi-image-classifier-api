import os
from django.db import models
from django.conf import settings

DATASET_DIR = os.path.join(settings.MEDIA_ROOT, 'dataset') # dataset directory
TEMP_UPLOADS_DIR = os.path.join(settings.MEDIA_ROOT, 'temp/uploads') # temp uploads directory

class UploadImage(models.Model):
    class_name = models.CharField(max_length=512)
    image = models.ImageField(upload_to=TEMP_UPLOADS_DIR, max_length=1024) # store the image in the media folder inside the temp/uploads folder
    
    class Meta:
        db_table = 'uploaded_images'
    
    # def save(self, *args, **kwargs):
    #     self.class_name = self.class_name.lower()
    #     super().save(*args, **kwargs)
        
    #     class_name_folder = os.path.join(DATASET_DIR, self.class_name)
    #     os.makedirs(class_name_folder, exist_ok=True) # create the class_name folder if it doesn't exist
        
    #     # Get the next numerical filename
    #     existing_files = [int(os.path.splitext(f)[0]) for f in os.listdir(class_name_folder) if f.split('.')[0].isdigit()]
    #     next_number = max(existing_files) + 1 if existing_files else 1
        
    #     new_path = os.path.join(class_name_folder, f"{next_number}{os.path.splitext(self.image.name)[1]}")
        
    #     os.rename(self.image.path, new_path)  # Move file to dataset
        
    #     # Update model file path
    #     self.image.name = os.path.relpath(new_path, settings.MEDIA_ROOT)
        
    #     # Save updated path to the database
    #     super().save(update_fields=['image'])
        
    #     # Remove the temp folder if empty
    #     if os.path.exists(TEMP_UPLOADS_DIR) and not os.listdir(TEMP_UPLOADS_DIR):
    #         os.rmdir(TEMP_UPLOADS_DIR)
    
    # Check if the directory exists, otherwise create it
    if not os.path.exists(TEMP_UPLOADS_DIR):
        os.makedirs(TEMP_UPLOADS_DIR, exist_ok=True)

    # Create your models here.
    
    def save(self, *args, **kwargs):
        self.class_name = self.class_name.lower()
        super().save(*args, **kwargs)
        
        class_name_folder = os.path.join(DATASET_DIR, self.class_name)
        os.makedirs(class_name_folder, exist_ok=True)  # create the class_name folder if it doesn't exist
        
        # Get the next numerical filename
        existing_files = [int(os.path.splitext(f)[0]) for f in os.listdir(class_name_folder) if f.split('.')[0].isdigit()]
        next_number = max(existing_files) + 1 if existing_files else 1
        
        new_path = os.path.join(class_name_folder, f"{next_number}{os.path.splitext(self.image.name)[1]}")
        
        os.rename(self.image.path, new_path)  # Move file to dataset
        
        # Update model file path
        self.image.name = os.path.relpath(new_path, settings.MEDIA_ROOT)
        
        # Save updated path to the database
        super().save(update_fields=['image'])
        
        # Remove the temp folder if empty
        if os.path.exists(TEMP_UPLOADS_DIR) and not os.listdir(TEMP_UPLOADS_DIR):
            os.rmdir(TEMP_UPLOADS_DIR)
        
    def __str__(self):
        return self.class_name

    @staticmethod
    def save_multiple(files, class_name):
        """Method to handle multiple file uploads"""
        instances = [UploadImage(class_name=class_name, image=file) for file in files]
        UploadImage.objects.bulk_create(instances)
