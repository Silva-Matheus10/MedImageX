from kafka import KafkaProducer
import io
from PIL import Image

def send_test_image():
    image = Image.new('RGB', (100, 100), color='red')  # Cria uma imagem vermelha
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    image_bytes = img_byte_arr.getvalue()

    producer = KafkaProducer(bootstrap_servers='localhost:9092')
    producer.send('image_topic', image_bytes)
    producer.flush()
    print("Imagem de teste enviada para o Kafka.")

send_test_image()
