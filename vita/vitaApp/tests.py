import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, butter, filtfilt

# 1. Définir les valeurs IR simulées (tu peux aussi les charger depuis un fichier ou ESP32)
import numpy as np

def generate_ir_signal(bpm=75, duration=60, sample_rate=100):
    """
    Génère un signal IR simulé pour une personne de 20 ans avec un rythme cardiaque stable.
    
    :param bpm: battements par minute
    :param duration: durée du signal en secondes
    :param sample_rate: nombre d'échantillons par seconde
    :return: liste de valeurs IR simulées
    """
    t = np.linspace(0, duration, duration * sample_rate)
    heart_rate_hz = bpm / 60.0
    baseline = 51500
    amplitude = 600  # légère variation autour du point moyen

    # Simuler un battement cardiaque avec bruit
    ir_signal = baseline + amplitude * np.sin(2 * np.pi * heart_rate_hz * t) + np.random.normal(0, 30, len(t))
    return ir_signal.astype(int).tolist()
# Répéter pour avoir 1000 points (10s à 100 Hz)
ir_values = generate_ir_signal(bpm=72, duration=10, sample_rate=100)  # 10 secondes de données simulées

# 2. Filtrage passe-bas
def butter_lowpass_filter(data, cutoff, fs, order=4):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

fs = 100  # fréquence d’échantillonnage
cutoff = 2.5  # Hz : fréquence de coupure
ir_filtered = ir_values

# 3. Détection des pics sur le signal filtré
peaks, _ = find_peaks(ir_filtered, distance=50, prominence=30)

# 4. Calcul de la fréquence cardiaque
duration_sec = len(ir_filtered) / fs
bpm = (len(peaks) / duration_sec) * 60

# 5. Tracé de l'onde filtrée
t = np.linspace(0, duration_sec, len(ir_filtered))

print(f"Fréquence cardiaque estimée : {bpm:.2f} BPM")

plt.plot(t, ir_filtered, label="Signal IR filtré")
plt.plot(t[peaks], np.array(ir_filtered)[peaks], 'ro', label='Pics détectés')
plt.title("Onde de pouls filtrée (passe-bas)")
plt.xlabel("Temps (s)")
plt.ylabel("Valeurs IR")
plt.grid()
plt.legend()
plt.tight_layout()
plt.show()