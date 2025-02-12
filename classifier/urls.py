from django.urls import path
from .views import UploadImageView, TrainModelView, PredictImageView


urlpatterns = [
    path('upload', UploadImageView.as_view(), name='upload-image'),
    path('train', TrainModelView.as_view(), name='train-model'),
    path('predict', PredictImageView.as_view(), name='predict-image'),
]
