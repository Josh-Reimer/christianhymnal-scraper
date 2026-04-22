import os
import librosa
import numpy as np
import soundfile as sf
from pydub import AudioSegment

INPUT_DIR = "mp3s"
OUTPUT_DIR = "music_chunks"
CHUNK_SECONDS = 20

os.makedirs(OUTPUT_DIR, exist_ok=True)


def is_music(y, sr):
    """
    Heuristic classifier:
    returns True if chunk is likely music/singing
    """

    # spectral centroid (lower = more harmonic)
    centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))

    # zero crossing rate (speech is higher)
    zcr = np.mean(librosa.feature.zero_crossing_rate(y))

    # energy variance (music sustains energy)
    rms = librosa.feature.rms(y=y)[0]
    energy_var = np.var(rms)

    # tuned for hymns / singing
    if centroid < 2500 and zcr < 0.1 and energy_var > 1e-6:
        return True

    return False


def split_mp3(path):
    audio = AudioSegment.from_mp3(path)
    duration_ms = len(audio)

    chunk_ms = CHUNK_SECONDS * 1000
    base = os.path.splitext(os.path.basename(path))[0]

    for i, start in enumerate(range(0, duration_ms, chunk_ms)):
        chunk = audio[start:start + chunk_ms]

        temp_path = "/tmp/chunk.wav"
        chunk.export(temp_path, format="wav")

        y, sr = librosa.load(temp_path, sr=None, mono=True)

        if is_music(y, sr):
            out_name = f"{base}_music_{i:04d}.wav"
            out_path = os.path.join(OUTPUT_DIR, out_name)
            sf.write(out_path, y, sr)
            print(f"✓ MUSIC → {out_name}")
        else:
            print(f"✗ speech/noise → {base}_{i:04d}")


for file in os.listdir(INPUT_DIR):
    if file.lower().endswith(".mp3"):
        print(f"\nProcessing {file}")
        split_mp3(os.path.join(INPUT_DIR, file))
