def create_windows(audio, sample_rate, window_seconds=1):
    window_size = sample_rate * window_seconds

    windows = []

    for start in range(0, len(audio), window_size):
        end = start + window_size

        if end <= len(audio):
            windows.append(audio[start:end])

    return windows


def resample_audio(audio, orig_sample_rate, target_sample_rate):
    """
    Resample audio to target_sample_rate if it doesn't already match.

    BUG FIX: nothing upstream was resampling incoming audio to the 16kHz
    AASIST-L expects (aasist_detector.py's SAMPLE_RATE constant was
    documentation only, not enforced). A file at any other native sample
    rate was fed to the model as-is, effectively at the wrong "speed" -
    confirmed this produces false spoof-risk inflation on genuine human
    speech recorded at a non-16kHz rate.
    """
    import numpy as np
    from scipy.signal import resample

    if orig_sample_rate == target_sample_rate:
        return np.asarray(audio, dtype=np.float32)

    n_target_samples = int(round(len(audio) * target_sample_rate / orig_sample_rate))
    resampled = resample(audio, n_target_samples)

    return resampled.astype(np.float32)