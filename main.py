from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import soundfile as sf
import io

from audio_pipeline import create_windows, resample_audio
from aasist_detector import AASISTDetector
from transcription import transcription_provider
from risk_engine import (
    detect_indicators,
    calculate_context_risk,
    calculate_action_risk,
    calculate_final_risk,
)


app = FastAPI(title="VoiceShield Backend")

# Without this, the browser blocks requests from the frontend dev server
# (e.g. localhost:5173) to this API (localhost:8000) - different ports
# count as different origins. Tightened to localhost dev ports here;
# add your deployed frontend's real origin before going beyond local testing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load AASIST-L once when backend starts
detector = AASISTDetector()


@app.get("/")
def home():
    return {
        "project": "VoiceShield Backend",
        "status": "Backend is running",
        "detector": "AASIST-L",
        "risk_engine": "connected",
    }


@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """
    Kept for backwards compatibility: voice-detection only, no risk fusion.
    Prefer /analyze-call for the full pipeline.
    """

    audio_data = await file.read()
    audio, sample_rate = sf.read(io.BytesIO(audio_data))

    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)

    duration = len(audio) / sample_rate

    # BUG FIX: resample to what AASIST-L actually expects (16kHz) before
    # doing anything else with it. Previously this was skipped entirely -
    # a file at any other native rate got fed to the model as-is, which
    # confirmed produces false spoof-risk inflation on genuine speech.
    original_sample_rate = sample_rate
    audio = resample_audio(audio, sample_rate, AASISTDetector.SAMPLE_RATE)
    sample_rate = AASISTDetector.SAMPLE_RATE

    # Harsh's 1s chunking - informational only, does not feed detection.
    # AASISTDetector windows the audio itself internally (4s windows, sized
    # to the model's expected input length) - this count is just a coarse
    # "how many 1s slices does this clip have" stat for the API consumer.
    informational_chunks = create_windows(audio, sample_rate, window_seconds=1)

    detection = detector.analyze(audio)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(audio_data),
        "original_sample_rate": original_sample_rate,
        "analyzed_sample_rate": sample_rate,
        "duration_seconds": round(duration, 2),
        "informational_1s_chunk_count": len(informational_chunks),
        "voice_detection": detection,
        "status": "Audio analyzed successfully",
    }


@app.post("/analyze-call")
async def analyze_call(
    file: UploadFile = File(...),
    transcript: Optional[str] = Form(None),
):
    """
    Full pipeline: voice spoof detection + (optional) transcript-based
    context/action risk indicators, fused into one final risk verdict.

    `transcript` is optional. If the caller already has one (e.g. from
    their own call-center STT), pass it as a form field. If omitted, this
    falls back to `transcription_provider` (currently a no-op stub - see
    transcription.py) and, failing that, to voice-only risk.
    """

    audio_data = await file.read()
    audio, sample_rate = sf.read(io.BytesIO(audio_data))

    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)

    duration = len(audio) / sample_rate

    # BUG FIX: see /upload-audio - same missing resample step, same fix.
    original_sample_rate = sample_rate
    audio = resample_audio(audio, sample_rate, AASISTDetector.SAMPLE_RATE)
    sample_rate = AASISTDetector.SAMPLE_RATE

    informational_chunks = create_windows(audio, sample_rate, window_seconds=1)

    # --- Voice channel (Sahil's AASIST-L) ---
    detection = detector.analyze(audio)
    voice_risk = detection["average_spoof_probability"]
    reliability = detection["reliability"]

    # --- Transcript channel (risk_engine) ---
    if transcript is None:
        transcript = transcription_provider.transcribe(audio, sample_rate)

    indicators = detect_indicators(transcript) if transcript else []
    context_risk = calculate_context_risk(indicators) if transcript else 0.0
    action_risk = calculate_action_risk(indicators)  # 0.10 baseline if indicators == []

    # --- Fusion ---
    final_risk = calculate_final_risk(
        voice_risk=voice_risk,
        context_risk=context_risk,
        action_risk=action_risk,
        reliability=reliability,
    )

    return {
        "filename": file.filename,
        "original_sample_rate": original_sample_rate,
        "analyzed_sample_rate": sample_rate,
        "duration_seconds": round(duration, 2),
        "informational_1s_chunk_count": len(informational_chunks),

        "voice_detection": detection,

        "transcript_used": transcript,
        "detected_indicators": indicators,
        "context_risk": round(context_risk, 3),
        "action_risk": round(action_risk, 3),

        "final_risk_assessment": final_risk,
    }
