import os
import yt_dlp
import json

def descargar_audio_youtube(video_url):
    """Descarga el audio del video de YouTube en formato MP3"""
    print(f"🔹 Descargando audio del video: {video_url}")
    #URLS = ['https://youtu.be/mBbcH47fLtU']
    output_path = '%(title)s.%(ext)s'
    #print(f"🔹 Descargando URLS: {URLS}")
    
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

video_url = str(input("Pega la URL del video a descargar: ")).strip()
descargar_audio_youtube(video_url)
