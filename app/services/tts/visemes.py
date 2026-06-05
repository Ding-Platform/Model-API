import numpy as np

USE_SMOOTH_WEIGHTS = True
FPS = 30

IPA_TO_VISEME = {
    "p": "Closed",
    "b": "Closed",
    "m": "Closed",
    "a": "Aa",
    "ɑ": "Aa",
    "æ": "Aa",
    "ʌ": "Aa",
    "ɒ": "Aa",
    "ɜ": "Aa",
    "ɝ": "Aa",
    "ə": "Aa",
    "ɚ": "Aa",
    "e": "Ee",
    "ɛ": "Ee",
    "i": "Ee",
    "ɪ": "Ee",
    "o": "oh",
    "ɔ": "oh",
    "u": "uh",
    "ʊ": "uh",
    "w": "uh",
    "y": "uh",
    "r": "uh",
    "ɹ": "uh",
    "ʃ": "uh",
    "ʒ": "uh",
    "tʃ": "uh",
    "dʒ": "uh",
    "t": "Ih",
    "d": "Ih",
    "k": "Ih",
    "g": "Ih",
    "ɡ": "Ih",
    "s": "Ih",
    "z": "Ih",
    "n": "Ih",
    "ŋ": "Ih",
    "j": "Ih",
    "h": "Ih",
    "l": "Ih",
    "θ": "Ih",
    "ð": "Ih",
    "ɾ": "Ih",
    "c": "Ih",
    "x": "Ih",
    "f": "Ih",
    "v": "Ih",
}


def generate_viseme_chunk(phonemes, audio_length, sample_rate, start_time):
    duration_sec = audio_length / sample_rate

    clean_ph = phonemes.replace("ˈ", "").replace("ˌ", "").replace("ː", "").replace("ˑ", "").replace("\u200d", "")

    if len(clean_ph) == 0:
        return [], start_time + duration_sec

    time_per_phoneme = duration_sec / len(clean_ph)
    chunk_timeline = []

    if not USE_SMOOTH_WEIGHTS:
        current_time = start_time
        last_viseme = "Closed"

        for p in clean_ph:
            if p in [".", ",", "!", "?"]:
                viseme = "Closed"
            elif p == " ":
                viseme = last_viseme
            else:
                viseme = IPA_TO_VISEME.get(p, "Ih")

            chunk_timeline.append({"time": round(current_time, 3), "value": viseme})
            last_viseme = viseme
            current_time += time_per_phoneme

        return chunk_timeline, start_time + duration_sec

    num_frames = max(1, int(np.ceil(duration_sec * FPS)))
    viseme_keys = ["Aa", "Ee", "Ih", "oh", "uh", "Closed"]

    raw_frames = {k: np.zeros(num_frames) for k in viseme_keys}

    for i in range(num_frames):
        t = i / FPS
        idx = int(t / time_per_phoneme)
        if idx >= len(clean_ph):
            idx = len(clean_ph) - 1

        p = clean_ph[idx]
        if p in [" ", ".", ",", "!", "?", "_", "-"]:
            v = "Closed"
        else:
            v = IPA_TO_VISEME.get(p, "Ih")

        raw_frames[v][i] = 1.0

    window_size = max(3, int(0.12 * FPS))
    smoothed_frames = {}

    for k in viseme_keys:
        padded = np.pad(raw_frames[k], (window_size // 2, window_size - 1 - window_size // 2), mode="edge")
        window = np.ones(window_size) / window_size
        smoothed_frames[k] = np.convolve(padded, window, mode="valid")

    for i in range(num_frames):
        frame_time = start_time + (i / FPS)

        total_w = sum(smoothed_frames[k][i] for k in viseme_keys)
        weights_dict = {}
        for k in viseme_keys:
            val = smoothed_frames[k][i] / total_w if total_w > 0 else 0.0
            weights_dict[k] = round(float(val), 3)

        chunk_timeline.append({"time": round(frame_time, 3), "weights": weights_dict})

    return chunk_timeline, start_time + duration_sec
