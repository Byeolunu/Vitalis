import json
import wave
import tempfile
from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from elevenlabs.client import ElevenLabs
from ollama import Client
import soundfile as sf
import os
from .forms import UserForm
from .models import User
import pyrebase
from django.shortcuts import get_object_or_404
import numpy as np


ollama_client = Client()
client_sound = ElevenLabs(api_key="sk_9d8240a9cb07e26c7417e02caddd689cc52419ffc18a970f")


def calculer_temperature_corporelle(valeurs_capteur):
    """
    Calcule la température corporelle à partir des valeurs brutes du capteur GY-906 / MLX90614.
    
    Args:
        valeurs_capteur (list or np.array): liste de 3000 valeurs de température (float)
    
    Returns:
        float: température corporelle moyenne (filtrée)
    """
    valeurs = np.array(valeurs_capteur)
    valeurs_filtrees = valeurs[(valeurs > 30.0) & (valeurs < 42.0)]  # plage normale pour la température corporelle
    valeurs_triees = np.sort(valeurs_filtrees)
    n = len(valeurs_triees)
    valeurs_trimmed = valeurs_triees[int(n * 0.1):int(n * 0.9)]
    temperature_moyenne = np.mean(valeurs_trimmed)

    return round(temperature_moyenne, 2)

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def afficher_ondes_pouls(ir_values):
    t = np.linspace(0, 30, len(ir_values))  
    plt.figure(figsize=(12, 4))
    plt.plot(t, ir_values, label='Signal IR (PPG)', color='blue')
    plt.xlabel('Temps (s)')
    plt.ylabel('Amplitude IR')
    plt.title('Onde de pouls (PPG)')
    plt.grid(True)
    plt.legend()
    plt.show()


def calculer_bpm(ir_values, fs=100):
    # Détection des pics (pics systoliques)
    peaks, _ = find_peaks(ir_values, distance=fs*0.5)  # au moins 0.5s entre 2 battements
    bpm = (len(peaks) / 30) * 60  # 30 secondes de données
    return round(bpm, 2)


def calculer_spo2(ir_values, red_values):
    ir_ac = np.std(ir_values)
    red_ac = np.std(red_values)
    ir_dc = np.mean(ir_values)
    red_dc = np.mean(red_values)

    # Ratio entre les signaux
    ratio = (red_ac / red_dc) / (ir_ac / ir_dc)

    # Formule empirique typique (MAX30100 datasheet)
    spo2 = 110 - 25 * ratio
    spo2 = np.clip(spo2, 0, 100)
    return round(spo2, 2)


def estimer_tension_art(peaks, fs=100): #peaks, _ = find_peaks(ir_values, distance=fs*0.5)
    rr_intervals = np.diff(peaks) / fs  # temps entre pics en secondes
    rr_mean = np.mean(rr_intervals)
    systolique = 120 + (0.5 * (1 - rr_mean)) * 100  # estimation très grossière
    diastolique = 80 + (0.3 * (1 - rr_mean)) * 100
    return round(systolique, 2), round(diastolique, 2)


def estimer_fatigue(peaks, fs=100): #peaks, _ = find_peaks(ir_values, distance=fs*0.5)
    rr_intervals = np.diff(peaks) / fs
    hrv = np.std(rr_intervals) * 1000  # en millisecondes

    # Plus HRV est faible → plus le corps est fatigué
    if hrv > 70:
        niveau = "Reposé"
    elif hrv > 50:
        niveau = "Normal"
    else:
        niveau = "Fatigué"

    return niveau, round(hrv, 2)
###################################################################################################################


def record_audio_from_file(audio_file):
    with open(audio_file, 'rb') as audio:
        return audio.read()


def transcribe_audio(audio_file):
    with audio_file.open('rb') if hasattr(audio_file, 'open') else audio_file as audio:
        response = client_sound.speech_to_text.convert(
            file=audio,
            model_id="scribe_v1"
        )
    return response.text



# def get_llm_response(prompt):
#     if not prompt:
#         return {'error': 'No input provided'}

#     response = ollama_client.chat(
#         model='vitalis_Q4_K_M',
#         messages=[{'role': 'user', 'content': prompt}]
#     )

#     return response['message']['content']

def get_llm_response(prompt, user_id=None):
    if not prompt:
        return {'error': 'No input provided'}

    context = ""
    if user_id:
        try:
            context = build_user_context(user_id)
        except Exception as e:
            context = "User information could not be loaded.\n\n"
            print(f"Error building user context: {e}")

    full_prompt = f"""
    You are Vitalis, a friendly and knowledgeable health assistant. You're having a conversation with the following user:

    {context}

    Always personalize your answers and use a warm, human tone.

    The user just said: "{prompt}"

    How would you respond?
    """

    response = ollama_client.chat(
        model='vitalis_Q4_K_M',
        messages=[{'role': 'user', 'content': full_prompt}]
    )
    print(f"Using context: {context}")

    return response['message']['content']


def speak_and_save_audio(text, filename="response.wav"):
    audio_stream = client_sound.text_to_speech.convert_as_stream(
        text=text,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2"
    )

    media_path = os.path.join('media', filename)
    with open(media_path, "wb") as f:
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                f.write(chunk)

    return f"/media/{filename}"


@csrf_exempt
@csrf_exempt
def transcribe(request):
    if request.method == 'POST':
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return JsonResponse({'error': 'No audio file provided'}, status=400)

        # Call transcription helper function instead of self
        transcribed_text = transcribe_audio(audio_file)
        return JsonResponse({'user_input': transcribed_text})

    return JsonResponse({'error': 'Invalid method'}, status=405)



@csrf_exempt
def predict(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            prompt = body.get('prompt', '')
            user_id = body.get('user_id')  # ✅ retrieve user_id from the request

            if not prompt:
                return JsonResponse({'error': 'No prompt provided'}, status=400)

            # ✅ pass user_id to personalize the response
            response_text = get_llm_response(prompt, user_id=user_id)
            audio_url = speak_and_save_audio(response_text)

            return JsonResponse({
                'prediction': response_text,
                'audio_url': audio_url
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid method'}, status=405)

def index(request):
    return render(request, 'final_index.html')

def welcome(request):
    user = request.user  # Assuming user is authenticated and has an ID
    if user.is_authenticated:
        return redirect('home', user_id=user.id)  # Redirecting with user_id
    else:
        return redirect('index')  # or handle unauthenticated users

# def heart_rate_view(request):
#     ref = db.reference('vitalis-1')
#     data = ref.get()
#
#     # Convert data to sorted list of (timestamp, bpm)
#     if data:
#         data_points = sorted([(int(ts), bpm) for ts, bpm in data.items()])
#     else:
#         data_points = []
#
#     # Prepare labels and values for Chart.js
#     labels = [str(ts) for ts, _ in data_points]
#     values = [bpm for _, bpm in data_points]
#
#     return render(request, 'heart_rate_chart.html', {
#         'labels': labels,
#         'values': values
#     })
def user_register(request, pk=None):
    if pk:
        user = get_object_or_404(User, pk=pk)
    else:
        user = None

    if request.method == 'POST':
        print("POST request received.")
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            print("Form is valid. Redirecting to homepage...")
            user = form.save()  # Save the form and get the user object
            return redirect('home', user_id=user.id)  # Redirect to home with user_id
        else:
            print("Form is invalid:", form.errors)
    else:
        print("GET request received.")
        form = UserForm(instance=user)

    return render(request, 'form.html', {'form': form, 'errors': form.errors})

config={
        'apiKey': "AIzaSyC_623bgmBP04JpVv8GnEfd58WzYgLMmbc",
       'authDomain': "vitalis-1.firebaseapp.com",
       'databaseURL': "https://vitalis-1-default-rtdb.firebaseio.com",
        'projectId': "vitalis-1",
        'storageBucket': "vitalis-1.firebasestorage.com",
        'messagingSenderId': "150195650266",
        'appId': "1:150195650266:web:e836be50305ff8de28afe3",
}

firebase = pyrebase.initialize_app(config)
authe=firebase.auth()
database=firebase.database()

def progress(request):
    return render(request, 'progress.html')

def index1(request):
    channel_name=database.child("data").child("temperature_ambiante").get().val()
    channel_age=database.child("data").child("temperature_corporelle").get().val()
    channel_sexe=database.child("data").child("timestamp").get().val()

    channel_tempamb=database.child("datas").child("valeur").child("temperature_ambiante").get().val()
    channel_tempcor=database.child("datas").child("valeur").child("temperature_corporelle").get().val()
    channel_spo=database.child("datas").child("valeur").child("spo2").get().val()



    return render(request, 'index1.html', {'channel_name': channel_name, 'channel_age': channel_age, 'channel_sexe': channel_sexe , 'channel_tempamb': channel_tempamb,'channel_tempcor':channel_tempcor,'channel_spo2':channel_spo})



def home(request,user_id=None):
    # Assuming you want to display details for a specific user
    user = get_object_or_404(User, id=user_id)  # Replace with actual logic to get user
    return render(request, 'homePage.html', {'user': user, 'user_id': user.id})


# def user_edit(request, user_id):
#     user = get_object_or_404(User, id=user_id)
#     if request.method == 'POST':
#         form = UserForm(request.POST, instance=user)
#         if form.is_valid():
#             form.save()
#             return redirect('home') 
#     else:
#         form = UserForm(instance=user)
#     return render(request, 'form.html', {'form': form})
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            # Pass the updated user data to the homepage
            return redirect('home', user_id=user.id)
    else:
        form = UserForm(instance=user)

    return render(request, 'form.html', {'form': form})



from vitaApp.models import User 






################################"
import threading
import time
import numpy as np
from scipy.signal import find_peaks
from firebase_admin import db
from .models import User
from django.shortcuts import get_object_or_404

# Global metrics cache
firebase_metrics = {
    'temperature': [],
    'bpm': [],
    'spo2': [],
    'systolic': [],
    'diastolic': [],
    'fatigue': None,
    'hrv': None
}

def collect_firebase_data_for_30_seconds():
    firebase_metrics = {}

    temperature_values = []
    ir_values = []
    red_values = []
    spo2 = []

    start = time.time()
    while time.time() - start < 30:
        try:
            data = database.child('datats/valeur').get().val()
            if data:
                temp = data.get('temperature_corporelle')
                ir = data.get('ir')
                red = data.get('red')
                spo = data.get('spo2')

                if temp: temperature_values.append(float(temp))
                if ir: ir_values.append(float(ir))
                if red: red_values.append(float(red))
                if spo: spo2.append(float(spo))

        except Exception as e:
            print("Error fetching from Firebase:", e)

        time.sleep(0.01)

    # Stockage des valeurs brutes
    firebase_metrics['temperature_raw'] = temperature_values
    firebase_metrics['bpm_raw'] = ir_values
    firebase_metrics['spo2_raw'] = spo2
    firebase_metrics['systolic_raw'] = red_values

    # Calculs
    firebase_metrics['temperature'] = calculer_temperature_corporelle(temperature_values)
    peaks, _ = find_peaks(ir_values, distance=50)
    firebase_metrics['bpm'] = calculer_bpm(ir_values)
    firebase_metrics['systolic'], firebase_metrics['diastolic'] = estimer_tension_art(peaks)
    firebase_metrics['fatigue'], firebase_metrics['hrv'] = estimer_fatigue(peaks)
    firebase_metrics['spo2'] = calculer_spo2(ir_values, red_values)

    return firebase_metrics


def start_collection_thread():
    thread = threading.Thread(target=collect_firebase_data_for_30_seconds)
    thread.start()

def build_user_context(user_id):
    user = get_object_or_404(User, id=user_id)
    age = user.get_age()

    context = f"""
    User Profile:
    - Name: {user.FirstName} {user.LastName}
    - Gender: {user.Gender}
    - Age: {age}
    - Height: {user.height} cm
    - Weight: {user.weight} kg
    """

    if firebase_metrics['temperature']:
        temp_avg = calculer_temperature_corporelle(firebase_metrics['temperature'])
        context += f"\n- Average Body Temp (30s): {temp_avg}°C"
    if firebase_metrics['bpm']:
        context += f"\n- Heart Rate: {firebase_metrics['bpm']} bpm"
    if firebase_metrics['spo2']:
        context += f"\n- SpO2: {firebase_metrics['spo2']}%"
    if firebase_metrics['systolic'] and firebase_metrics['diastolic']:
        context += f"\n- Blood Pressure: {firebase_metrics['systolic']}/{firebase_metrics['diastolic']} mmHg"
    if firebase_metrics['fatigue']:
        context += f"\n- Fatigue Level: {firebase_metrics['fatigue']} (HRV: {firebase_metrics['hrv']} ms)"

    return context.strip()

# def render_health_metrics(request):
#     # Récupérer les données de Firebase
#     firebase_metrics = collect_firebase_data_for_30_seconds()
#
#     # Extraction des valeurs nécessaires
#     ir_values = firebase_metrics['bpm']
#     red_values = firebase_metrics['systolic']
#     temperature_values = firebase_metrics['temperature']
#     spo2 = firebase_metrics['spo2']
#
#     # Calculs
#     bpm = calculer_bpm(ir_values)
#     peaks, _ = find_peaks(ir_values, distance=100*0.5)
#     systolic, diastolic = estimer_tension_art(peaks)
#     niveau_fatigue, hrv = estimer_fatigue(peaks)
#     temp_avg = calculer_temperature_corporelle(temperature_values)
#
#     # Préparer le contexte pour le template
#     context = {
#         'bpm': bpm,
#         'spo2': spo2,
#         'systolic': systolic,
#         'diastolic': diastolic,
#         'niveau_fatigue': niveau_fatigue,
#         'hrv': hrv,
#         'temperature': temp_avg,
#     }
#
#     return render(request, 'homePage.html', context)

# def data(request):
#     firebase_metrics = collect_firebase_data_for_30_seconds()
#
#     return render(request, 'data.html', {'firebase_metrics': firebase_metrics})


# def get_metrics_data(request):
#     # Refresh data before serving
#     collect_firebase_data_for_30_seconds()
#
#     def convert_to_float(data_list):
#         return [float(item) if isinstance(item, (int, float, str)) else 0 for item in data_list]
#
#     data['temperature'] = convert_to_float(data['temperature'])
#     data['bpm'] = convert_to_float(data['bpm'])
#     data['spo2'] = convert_to_float(data['spo2'])
#     data['fatigue'] = convert_to_float(data['fatigue'])
#
#     return JsonResponse(data)


# def metrics_data(request):
#     firebase_metrics = collect_firebase_data_for_30_seconds()
#
#     # Créer des labels temporels fictifs (ou à partir du timestamp)
#     labels = [str(i) for i in range(len(firebase_metrics.get('temperature_raw', [])))]
#
#     return JsonResponse({
#         "temperature": firebase_metrics.get("temperature_raw", []),
#         "bpm": firebase_metrics.get("bpm_raw", []),
#         "spo2": firebase_metrics.get("spo2_raw", []),
#         "fatigue": [firebase_metrics.get("fatigue", 0)] * len(labels),  # si une seule valeur
#         "labels": labels
#     })
#

import numpy as np
from scipy.signal import find_peaks

def moyenne(liste):
    return round(sum(liste) / len(liste), 2) if liste else 0

def calculer_spo2(ir_values, red_values):
    if not ir_values or not red_values:
        return 0
    try:
        ac_ir = max(ir_values) - min(ir_values)
        dc_ir = sum(ir_values) / len(ir_values)
        ac_red = max(red_values) - min(red_values)
        dc_red = sum(red_values) / len(red_values)

        r = (ac_red / dc_red) / (ac_ir / dc_ir)
        spo2 = 110 - 25 * r
        return round(spo2, 2)
    except:
        return 0

def calculer_bpm(ir_values):
    peaks, _ = find_peaks(ir_values, distance=50)
    if len(peaks) < 2:
        return 0
    intervals = np.diff(peaks) * 0.01  # 0.01s entre deux mesures
    bpm = 60 / np.mean(intervals)
    return round(bpm, 2)

def estimer_tension(bpm):
    systolic = 0.5 * bpm + 80
    diastolic = 0.3 * bpm + 40
    return round(systolic), round(diastolic)

def data(request):
    firebase_metrics = collect_firebase_data_for_30_seconds()

    ir_values = firebase_metrics.get('bpm_raw', [])
    red_values = firebase_metrics.get('systolic_raw', [])
    temp_values = firebase_metrics.get('temperature_raw', [])
    spo2_values = firebase_metrics.get('spo2_raw', [])

    # Calculs selon les capteurs
    bpm = calculer_bpm(ir_values)
    spo2 = calculer_spo2(ir_values, red_values)
    temperature = moyenne(temp_values)
    systolic, diastolic = estimer_tension(bpm)

    moyennes = {
        'temperature_moyenne': temperature,
        'bpm_moyen': bpm,
        'spo2_moyen': spo2,
        'tension_systolique': systolic,
        'tension_diastolique': diastolic,
        'niveau_fatigue': firebase_metrics.get('fatigue', 'Inconnu')
    }

    return render(request, 'data.html', {
        'firebase_metrics': firebase_metrics,
        'moyennes': moyennes
    })
