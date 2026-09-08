import os
import time
import numpy as np
import torch

from _net import Model


class AASISTDetector:

    SAMPLE_RATE = 16000
    TARGET_LENGTH = 64600
    WINDOW_SECONDS = 4.0
    WINDOW_SAMPLES = 64600

    def __init__(self, weights_path=None):

        if weights_path is None:
            weights_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "weights",
                "AASIST-L.pth"
            )

        self.device = torch.device("cpu")

        config = {
            "architecture": "AASIST",
            "nb_samp": 64600,
            "first_conv": 128,
            "filts": [
                70,
                [1, 32],
                [32, 32],
                [32, 24],
                [24, 24]
            ],
            "gat_dims": [24, 32],
            "pool_ratios": [0.4, 0.5, 0.7, 0.5],
            "temperatures": [2.0, 2.0, 100.0, 100.0]
        }

        if not os.path.exists(weights_path):
            raise FileNotFoundError(
                f"AASIST-L weights not found: {weights_path}"
            )

        self.model = Model(config)

        checkpoint = torch.load(
            weights_path,
            map_location="cpu"
        )

        if isinstance(checkpoint, dict):
            checkpoint = checkpoint.get(
                "state_dict",
                checkpoint
            )

        self.model.load_state_dict(
            checkpoint,
            strict=True
        )

        self.model.eval()

    @staticmethod
    def prepare_audio(audio):

        audio = np.asarray(
            audio,
            dtype=np.float32
        ).reshape(-1)

        if len(audio) >= AASISTDetector.TARGET_LENGTH:
            return audio[:AASISTDetector.TARGET_LENGTH]

        if len(audio) == 0:
            raise ValueError("Audio is empty")

        repeats = (
            AASISTDetector.TARGET_LENGTH // len(audio)
        ) + 1

        audio = np.tile(
            audio,
            repeats
        )

        return audio[:AASISTDetector.TARGET_LENGTH]

    def create_windows(self, audio):

        audio = np.asarray(
            audio,
            dtype=np.float32
        ).reshape(-1)

        windows = []

        step = self.WINDOW_SAMPLES

        for start in range(
            0,
            len(audio),
            step
        ):

            end = start + step

            chunk = audio[start:end]

            if len(chunk) == 0:
                continue

            chunk = self.prepare_audio(chunk)

            windows.append(chunk)

            if end >= len(audio):
                break

        return windows

    @torch.no_grad()
    def predict_window(self, audio):

        audio = self.prepare_audio(audio)

        tensor = torch.from_numpy(
            audio
        ).unsqueeze(0)

        _, logits = self.model(tensor)

        probabilities = torch.softmax(
            logits,
            dim=1
        )[0]

        spoof_probability = float(
            probabilities[0].item()
        )

        bona_fide_probability = float(
            probabilities[1].item()
        )

        return {
            "spoof_probability": round(
                spoof_probability,
                4
            ),
            "bona_fide_probability": round(
                bona_fide_probability,
                4
            )
        }

    def analyze(self, audio):

        start_time = time.perf_counter()

        windows = self.create_windows(audio)

        if not windows:
            raise ValueError(
                "No valid audio windows created"
            )

        window_results = []

        for index, window in enumerate(windows):

            result = self.predict_window(
                window
            )

            result["window"] = index + 1

            window_results.append(result)

        spoof_scores = [
            result["spoof_probability"]
            for result in window_results
        ]

        bona_fide_scores = [
            result["bona_fide_probability"]
            for result in window_results
        ]

        average_spoof = float(
            np.mean(spoof_scores)
        )

        average_bona_fide = float(
            np.mean(bona_fide_scores)
        )

        maximum_spoof = float(
            np.max(spoof_scores)
        )

        # NOTE / ASSUMPTION: nothing in the original files defined "reliability".
        # Interpreting it here as cross-window agreement: if every ~4s window of
        # the same call gives a similar spoof score, the reading is more
        # trustworthy; if scores swing wildly window-to-window, trust it less.
        # Single-window calls (short clips) get reliability = 1.0 since there is
        # nothing to compare across. Flag this to your team/mentor for review —
        # it's a reasonable placeholder, not a validated metric.
        if len(spoof_scores) > 1:
            score_std = float(np.std(spoof_scores))
            reliability = max(0.0, 1.0 - min(score_std * 2, 1.0))
        else:
            reliability = 1.0

        if average_spoof >= 0.75:
            risk_level = "CRITICAL"

        elif average_spoof >= 0.40:
            risk_level = "MEDIUM"

        else:
            risk_level = "LOW"

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        return {
            "model": "AASIST-L",
            "sample_rate": self.SAMPLE_RATE,
            "window_duration_seconds": self.WINDOW_SECONDS,
            "windows_analyzed": len(windows),

            "average_spoof_probability": round(
                average_spoof,
                4
            ),

            "average_bona_fide_probability": round(
                average_bona_fide,
                4
            ),

            "maximum_spoof_probability": round(
                maximum_spoof,
                4
            ),

            "risk_level": risk_level,

            "reliability": round(
                reliability,
                4
            ),

            "latency_ms": round(
                latency_ms,
                2
            ),

            "window_results": window_results
        }