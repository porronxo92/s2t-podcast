import os
import yt_dlp
import json
from flask import Flask, request, jsonify
from google.cloud import storage, speech
import google.generativeai as genai

# Configuración de Google Cloud
BUCKET_NAME = "podcast-yt"
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)

def descargar_audio_youtube(video_url):
    """Descarga el audio del video de YouTube en formato MP3"""
    print(f"🔹 Descargando audio del video: {video_url}")
    output_path = '%(title)s.%(ext)s'
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        'outtmpl': output_path,
        'noplaylist': True,  # Evitar que intente descargar playlists
        'extractaudio': True  # Asegurarse de que solo extraiga el audio
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        print("✅ Audio descargado correctamente.")
        return output_path
    except Exception as e:
        print(f"❌ Error al descargar el audio: {e}")
        return None

def subir_a_gcs(local_path, bucket_name, destination_blob_name):
    """Sube un archivo a Google Cloud Storage"""
    print(f"🔹 Subiendo {local_path} a Google Cloud Storage Bucket:({bucket_name})...")
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(local_path)
        gcs_uri = f"gs://{bucket_name}/audios/{destination_blob_name}"
        print(f"✅ Archivo subido a {gcs_uri}")
        return gcs_uri
    except Exception as e:
        print(f"❌ Error al subir a GCS: {e}")
        return None

def transcribir_audio(gcs_uri):
    """Transcribe un archivo de audio almacenado en Cloud Storage"""
    print(f"🔹 Iniciando transcripción del audio en {gcs_uri}...")
    
    try:
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(uri=gcs_uri)

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="es-ES"
        )

        response = client.recognize(config=config, audio=audio)
        texto = " ".join([result.alternatives[0].transcript for result in response.results])
        
        print(f"✅ Transcripción completada. Texto obtenido:\n{texto[:200]}...")  # Muestra solo los primeros 200 caracteres
        return texto
    except Exception as e:
        print(f"❌ Error en la transcripción: {e}")
        return None

def analizar_texto_con_gemini(texto):
    """Analiza el texto usando Gemini y devuelve un resumen"""
    print("🔹 Enviando transcripción a Gemini para análisis...")
    
    try:
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"Resumen del podcast:\n\n{texto}\n\nExtrae los puntos clave."
        response = model.generate_content(prompt)
        resumen = response.text if response.text else "No se pudo analizar el texto."

        print(f"✅ Resumen generado:\n{resumen[:200]}...")  # Muestra solo los primeros 200 caracteres
        return resumen
    except Exception as e:
        print(f"❌ Error en el análisis con Gemini: {e}")
        return None

@app.route("/procesar", methods=["POST"])
def procesar_podcast():
    """Endpoint para procesar un podcast a partir de una URL de YouTube"""
    data = request.get_json()
    video_url = data.get("video_url")

    if not video_url:
        print("❌ Error: No se recibió una URL de video")
        return jsonify({"error": "Falta la URL del video"}), 400

    print("🔹 Iniciando procesamiento del podcast...")

    # Descarga el audio
    audio_path = descargar_audio_youtube(video_url)
    if not audio_path:
        return jsonify({"error": "No se pudo descargar el audio"}), 500

    # Sube el audio a GCS
    gcs_uri = subir_a_gcs(audio_path, BUCKET_NAME, audio_path)
    if not gcs_uri:
        return jsonify({"error": "No se pudo subir el archivo a GCS"}), 500

    # Transcribe el audio
    texto_transcrito = transcribir_audio(gcs_uri)
    if not texto_transcrito:
        return jsonify({"error": "No se pudo transcribir el audio"}), 500

    # Analiza la transcripción con Gemini
    resumen = analizar_texto_con_gemini(texto_transcrito)
    if not resumen:
        return jsonify({"error": "No se pudo generar el resumen con Gemini"}), 500

    print("✅ Proceso finalizado correctamente.")
    return jsonify({"transcripcion": texto_transcrito, "resumen": resumen})
    
@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    video_url = data.get("video_url")
    
    if not video_url:
        return jsonify({"error": "No se proporcionó una URL"}), 400

    # Descarga el audio
    audio_path = descargar_audioYT_bucket(video_url)
    if not audio_path:
        return jsonify({"error": "No se pudo descargar el audio"}), 500

    # Sube el audio a GCS
    gcs_uri = subir_a_gcs(audio_path, BUCKET_NAME, audio_path)
    if not gcs_uri:
        return jsonify({"error": "No se pudo subir el archivo a GCS"}), 500
       
    if gcs_uri:
        return jsonify({"message": "Descarga completada", "Ruta del archivo": gcs_uri})
    else:
        return jsonify({"error": "Error en la descarga"}), 500
        

def descargar_audioYT_bucket(video_url):
    """Descarga el audio del video de YouTube en formato MP3"""
    print(f"🔹 Descargando audio del video: {video_url}")

    output_path = '%(title)s.%(ext)s'
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        'outtmpl': output_path,
        'noplaylist': True,
        'extractaudio': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        print("✅ Audio descargado correctamente.")
        return output_path
    except Exception as e:
        print(f"❌ Error al descargar el audio: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Iniciando servidor Flask en Cloud Run...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
