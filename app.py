from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from azure.cognitiveservices.vision.customvision.training.models import ImageFileCreateBatch, ImageFileCreateEntry, Region
from msrest.authentication import ApiKeyCredentials
import os
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from PIL import ImageGrab
import io
import logging
import time
from kafka import KafkaProducer, KafkaConsumer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ENDPOINT = "https://medimagexinst-prediction.cognitiveservices.azure.com/"
PUBLISH_ITERATION_NAME = "MedImageModel"
prediction_key = "ddede9a12ed641c785846b3c03cac169"
PROJECT_ID = "0315eb64-8c95-478c-99ee-26edd5aa02f7"

credentials = ApiKeyCredentials(in_headers={"Prediction-key": prediction_key})
predictor = CustomVisionPredictionClient(ENDPOINT, credentials)


st.set_page_config(page_title="MedImageX", page_icon="🧑‍⚕️", layout="wide")

st.markdown(
    """
    <style>
    .st-emotion-cache-1dp5vir {
        background: linear-gradient(90deg, rgba(226,107,238,1) 0%, rgba(146,64,233,1) 69%);
}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    .typed-title {
        font-size: 45px;
        font-weight: bold;
        text-align: center;
        margin: 0 auto;
        font-family: "Source Sans Pro", sans-serif;
        overflow: hidden;
        white-space: nowrap;
        border-right: 0.15em solid purple;
        animation: typing 3s steps(30) 1s 1 normal both,
                   blink-caret 0.75s steps(30) infinite;
    }

    @keyframes typing {
        from { width: 0%; }
        to { width: 60%; }
    }

    @keyframes blink-caret {
        from, to { border-color: transparent; }
        50% { border-color: transparent; }
    }
    </style>

    <div class="typed-title">MedImageX</div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        if st.button("Login"):
            if username == 'user' and password == 'senha':
                st.session_state.logged_in = True
                st.success("Login executado com sucesso!")
            else:
                st.error("As credenciais estão incorretas. Tente novamente.")
else:
    aba1, aba2 = st.tabs(['Consulta de Exames', 'Consulta de Resultados'])

    with aba1:
        with st.sidebar:
            st.title("Conceitos")
        with st.sidebar.expander("O que é Machine Learning"):
            st.write('''
                O machine learning (ML) é o subconjunto da inteligência artificial (IA) que se concentra na construção de sistemas
                que aprendem, ou melhoram o desempenho, com base nos dados que consomem. A inteligência artificial é um termo amplo
                que se refere a sistemas ou máquinas que imitam a inteligência humana.
            ''')
            st.image("AI-ML-DL.webp")
        with st.sidebar.expander("O que é Visão computacional"):
            st.write('''
                A visão computacional é uma tecnologia que as máquinas usam para reconhecer imagens automaticamente
                e descrevê-las com precisão e eficiência.
            ''')
            st.image("Computer-Vision-pixforce-drone-1280x640.jpg")
        with st.sidebar.expander("O que é Kafka"):
            st.write('''
                O Apache Kafka é uma plataforma distribuída de transmissão de dados que é capaz de publicar, subscrever, armazenar e processar fluxos de registro em tempo real.
                Essa plataforma foi desenvolvida para processar fluxos de dados provenientes de diversas fontes e entregá-los a vários clientes. Em resumo, o Apache Kafka movimenta
                volumes imensos de dados não apenas do ponto A ao ponto B, mas também de A a Z e para qualquer outro local que você precisar simultaneamente.
            ''')
            st.image("images.png")
        with st.sidebar.expander("Imagens de Teste"):
            st.image("KCN_20_Elv_P.jpg")
            st.image("KCN_47_Sag_A.jpg")
            st.image("NOR_32_Elv_P.jpg")
            st.image("NOR_43_Sag_A.jpg")
            st.image("SUSP_43_Sag_A.jpg")
        st.header("Formulário de Dados do Paciente")
        st.write("Por favor, preencha os dados abaixo e insira a imagem do exame.")

        col1, col2, col3 = st.columns(3)

        with col1:
            nome = st.text_input("Nome")
        with col2:
            altura = st.text_input("Altura (em cm)")
        with col3:
            idade = st.text_input("Idade")

        doenca = st.selectbox("Informe a doença:", ("Ceratocone", "Glaucoma", "Catarata"))

        def serialize_image(image):
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()

        def send_image_kafka(image_bytes):
            logging.info("Iniciando Kafka producer...")
            try:
                producer = KafkaProducer(bootstrap_servers='localhost:9092')
                producer.send('image_topic', image_bytes)
                producer.flush()
                st.success("Imagem enviada com sucesso para o Kafka!")
                logging.info("Imagem enviada com sucesso para o Kafka.")
            except Exception as e:
                st.error(f"Erro ao enviar imagem para o Kafka: {e}")
                logging.error(f"Erro ao enviar imagem para o Kafka: {e}")

        def process_image():
            imagem = ImageGrab.grabclipboard()
            if imagem is not None:
                st.write('Imagem copiada da área de transferência')
                image_bytes = serialize_image(imagem)
                send_image_kafka(image_bytes)
            else:
                st.error("Não há imagem na área de transferência")

        st.header("Envio de Imagens para o Kafka")
        if st.button("Processar Imagem e Enviar para Kafka"):
            process_image()

        if 'results_data' not in st.session_state:
            st.session_state['results_data'] = {}

        def send_image_azure(placeholder):
            try:
                consumer = KafkaConsumer('image_topic',
                                        bootstrap_servers='localhost:9092',
                                        auto_offset_reset='latest',
                                        enable_auto_commit=False,
                                        group_id='meu-grupo')

                placeholder.write("Aguardando a classificação da imagem...")

                for message in consumer:
                    image_data = message.value
                    results = predictor.classify_image(PROJECT_ID, PUBLISH_ITERATION_NAME, image_data)
                    consumer.commit()
                    st.session_state['results_data'].clear()

                    for prediction in results.predictions:
                        tag_name = prediction.tag_name
                        probabilidade = prediction.probability * 100
                        logging.info(f'{tag_name}: {probabilidade:.2f}%')

                        st.session_state['results_data'][tag_name] = probabilidade
                        logging.info(f"Resultado adicionado ao dicionário: {tag_name} com {probabilidade:.2f}%")

                    with aba2:
                        st.header("Resultados da análise do exame")
                        for tag_name, probabilidade in st.session_state['results_data'].items():
                            st.markdown(f'**{tag_name}**: {probabilidade:.2f}%')
                            st.progress(probabilidade / 100)

                    break  
            except Exception as azure_error:
                logging.error(f"Erro ao enviar imagem para Azure: {azure_error}")
                placeholder.error(f"Erro ao enviar imagem para Azure: {azure_error}")

        
        if st.button("Iniciar Classificação"):
            result_placeholder = st.empty()
            send_image_azure(result_placeholder)
        
        

        
        

       
