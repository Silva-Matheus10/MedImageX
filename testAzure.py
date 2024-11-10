# <snippet_imports>
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from azure.cognitiveservices.vision.customvision.training.models import ImageFileCreateBatch, ImageFileCreateEntry, Region
from msrest.authentication import ApiKeyCredentials
import os, time, uuid

ENDPOINT = "https://medimagexinst-prediction.cognitiveservices.azure.com/"
PUBLISH_ITERATION_NAME = "MedImageModel"
prediction_key = "ddede9a12ed641c785846b3c03cac169"
PROJECT_ID = "0315eb64-8c95-478c-99ee-26edd5aa02f7"
IMAGE_PATH = "SUSP_21_EC_P.jpg"


credentials = ApiKeyCredentials(in_headers={"Prediction-key": prediction_key})
predictor = CustomVisionPredictionClient(ENDPOINT, credentials)

with open(IMAGE_PATH, mode="rb") as image_file:
    results = predictor.classify_image(PROJECT_ID, PUBLISH_ITERATION_NAME, image_file.read())

# Exibir resultados
for prediction in results.predictions:
    print(f'{prediction.tag_name}: {prediction.probability * 100:.2f}%')
