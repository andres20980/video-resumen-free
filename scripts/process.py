#!/usr/bin/env python3
"""resumen-video — 100% free video summarization.

Pipeline: yt-dlp (download) → ffmpeg (extract) → Gemini 2.5 Flash (transcribe + analyze + summarize)
Cost: $0.00 — everything runs on Gemini free tier.
"""

import os
import sys
import subprocess
import tempfile
import glob
import time
import io
from pathlib import Path
from datetime import datetime

from google import genai
from google.genai import types
from PIL import Image

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
GEMINI_FALLBACK_MODELS = os.environ.get(
    "GEMINI_FALLBACK_MODELS", "gemini-2.5-flash,gemini-2.5-pro"
).split(",")


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ─── Video Download ───────────────────────────────────────────────────────────

def download_video(url, output_dir):
    """Download video using yt-dlp, or copy if local file."""
    # Handle local files
    if os.path.isfile(url):
        import shutil
        dest = os.path.join(output_dir, "video" + os.path.splitext(url)[1])
        shutil.copy2(url, dest)
        return dest

    output_template = os.path.join(output_dir, "video.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--no-overwrites",
        "-o", output_template,
        url,
    ]
    subprocess.run(cmd, check=True)
    files = glob.glob(os.path.join(output_dir, "video.*"))
    if not files:
        raise FileNotFoundError("Download produced no files")
    return files[0]


def get_video_title(url):
    """Get video title via yt-dlp or filename for local files."""
    if os.path.isfile(url):
        return Path(url).stem
    try:
        result = subprocess.run(
            ["yt-dlp", "--get-title", "--no-playlist", url],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


# ─── ffmpeg Extraction ────────────────────────────────────────────────────────

def get_duration(video_path):
    """Get video duration in seconds."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def extract_audio(video_path, output_dir):
    """Extract audio as MP3 64kbps (small for Gemini upload)."""
    audio_path = os.path.join(output_dir, "audio.mp3")
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "libmp3lame", "-b:a", "64k",
        "-ar", "16000", "-ac", "1",
        audio_path, "-y",
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return audio_path


def extract_frames(video_path, output_dir, max_frames=20):
    """Extract evenly-spaced keyframes as JPEG."""
    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    duration = get_duration(video_path)
    # Short videos: at least 1 frame/sec, cap at max_frames
    # Long videos: 1 frame every 30s minimum
    if duration <= 60:
        n_frames = min(max_frames, max(1, int(duration)))
        interval = duration / n_frames
    else:
        interval = max(30, duration / max_frames)

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps=1/{interval}",
        "-frames:v", str(max_frames),
        "-q:v", "3",
        os.path.join(frames_dir, "frame_%03d.jpg"), "-y",
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))


# ─── Gemini AI ────────────────────────────────────────────────────────────────

MAX_RETRIES = 5
RETRY_BASE_DELAY = 10  # seconds


def get_client(api_key):
    return genai.Client(api_key=api_key)


def gemini_call(client, **kwargs):
    """Call Gemini with retry on 429/503, then fallback to alternative models."""
    from google.genai.errors import ServerError, ClientError

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return client.models.generate_content(**kwargs)
        except (ServerError, ClientError) as e:
            code = getattr(e, "code", 0) or 0
            if code in (429, 503) and attempt < MAX_RETRIES:
                wait = RETRY_BASE_DELAY * attempt
                log(f"⏳ Gemini {code} — retrying in {wait}s (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(wait)
            elif code in (429, 503):
                # Primary model exhausted retries — try fallback models
                original_model = kwargs.get("model", GEMINI_MODEL)
                for fallback in GEMINI_FALLBACK_MODELS:
                    fallback = fallback.strip()
                    if not fallback or fallback == original_model:
                        continue
                    log(f"🔄 {original_model} unavailable, trying fallback: {fallback}")
                    kwargs["model"] = fallback
                    try:
                        return client.models.generate_content(**kwargs)
                    except (ServerError, ClientError) as fb_err:
                        fb_code = getattr(fb_err, "code", 0) or 0
                        if fb_code in (429, 503):
                            log(f"⏳ Fallback {fallback} also returned {fb_code}")
                            continue
                        raise
                raise
            else:
                raise


def transcribe_audio(audio_path, api_key):
    """Transcribe audio using Gemini (free)."""
    client = get_client(api_key)

    log("Uploading audio to Gemini File API...")
    audio_file = client.files.upload(file=audio_path)

    # Poll until processing completes
    for _ in range(120):
        audio_file = client.files.get(name=audio_file.name)
        if audio_file.state.name == "ACTIVE":
            break
        if audio_file.state.name == "FAILED":
            raise RuntimeError("Gemini audio processing failed")
        time.sleep(3)
    else:
        raise RuntimeError("Gemini audio processing timed out")

    log("Transcribing with Gemini...")
    prompt = (
        "Transcribe este audio completo en español de forma literal y exhaustiva. "
        "Requisitos:\n"
        "- Transcripción COMPLETA palabra por palabra\n"
        "- Mantén el idioma original\n"
        "- Incluye muletillas, repeticiones y pausas naturales\n"
        "- NO resumas, NO omitas, NO parafrasees\n"
        "- Formato: texto corrido sin timestamps\n"
        "- Si el audio NO contiene habla humana (solo música, ruido, silencio), "
        "responde EXACTAMENTE: [SIN HABLA: descripción breve del audio]\n"
        "- NUNCA inventes palabras que no se escuchen\n"
    )
    response = gemini_call(
        client,
        model=GEMINI_MODEL,
        contents=[
            prompt,
            types.Part.from_uri(file_uri=audio_file.uri, mime_type=audio_file.mime_type),
        ],
        config=types.GenerateContentConfig(
            max_output_tokens=8192,
            temperature=0.1,
        ),
    )

    # Clean up remote file
    try:
        client.files.delete(name=audio_file.name)
    except Exception:
        pass

    return response.text


def analyze_frames(frame_paths, api_key):
    """Analyze frames using Gemini vision (free)."""
    client = get_client(api_key)

    if not frame_paths:
        return "[SIN FRAMES: no se extrajeron imágenes del video]"

    prompt = (
        "Analiza estas imágenes extraídas de un video. Para cada imagen relevante:\n"
        "1. Describe EXACTAMENTE qué se ve (objetos, personas, entorno, pantallas)\n"
        "2. Transcribe TODO el texto visible en pantalla literalmente\n"
        "3. Identifica logos, diagramas, datos numéricos, gráficos\n"
        "4. Agrupa imágenes similares para evitar repetición\n\n"
        "REGLA CRÍTICA: Describe SOLO lo que realmente aparece en las imágenes. "
        "NUNCA inventes contenido, texto, personas o elementos que no estén visibles. "
        "Si una imagen muestra un objeto simple (ej: un aparato), descríbelo tal cual."
    )
    parts = [prompt]

    for fp in frame_paths:
        img = Image.open(fp)
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        parts.append(types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"))

    log(f"Analyzing {len(frame_paths)} frames with Gemini vision...")
    response = gemini_call(
        client,
        model=GEMINI_MODEL,
        contents=parts,
        config=types.GenerateContentConfig(
            max_output_tokens=4096,
            temperature=0.2,
        ),
    )
    return response.text


import re

def sanitize_transcript(text):
    """Mask sensitive patterns that trigger Gemini PROHIBITED_CONTENT filter."""
    # Passwords and secrets in key=value or key: value form
    text = re.sub(
        r'(?i)(password|passwd|pwd|secret|token|api[_-]?key|credentials?)\s*[:=]\s*\S+',
        r'\1=***REDACTED***', text)
    # Connection strings (jdbc, postgres, mysql, mongo, redis, amqp…)
    text = re.sub(
        r'(?i)(jdbc|postgres(ql)?|mysql|mongodb(\+srv)?|redis|amqps?|https?)://\S+',
        '[CONNECTION_STRING_REDACTED]', text)
    # AWS-style keys (AKIA…)
    text = re.sub(r'AKIA[0-9A-Z]{16}', '***AWS_KEY***', text)
    # Generic long hex/base64 secrets (32+ chars)
    text = re.sub(r'(?<![a-zA-Z0-9])[A-Za-z0-9+/]{40,}={0,2}(?![a-zA-Z0-9])', '***LONG_SECRET***', text)
    # IPv4 addresses (internal IPs that may trigger filters)
    text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP_REDACTED]', text)
    return text


def generate_summary(transcript, visual_analysis, duration_min, api_key):
    """Generate comprehensive summary using Gemini (free)."""
    client = get_client(api_key)

    # Detect low-content scenarios
    no_speech = "[SIN HABLA" in transcript
    no_frames = "[SIN FRAMES" in visual_analysis
    low_content = no_speech or no_frames or len(transcript.strip()) < 50

    hallucination_guard = ""
    if low_content:
        hallucination_guard = (
            "\n\nALERTA DE CONTENIDO ESCASO:\n"
            "La transcripción y/o el análisis visual indican que este video tiene "
            "poco contenido verbal o visual significativo. "
            "En este caso DEBES:\n"
            "- Describir SOLO lo que realmente se ve y se oye\n"
            "- Si no hay habla, decir explícitamente que no hay habla\n"
            "- NO inventar presentaciones, diapositivas, webinars ni contenido ficticio\n"
            "- NO fabricar nombres de empresas, personas ni datos\n"
            "- Generar un resumen breve y honesto acorde al contenido real\n"
            "- Es preferible un resumen de 3 líneas honestas que uno de 100 líneas inventadas\n"
        )

    prompt = f"""Eres un experto en generar resúmenes exhaustivos de videos.
A partir de la transcripción y el análisis visual de un video de {duration_min:.1f} minutos,
genera un resumen COMPLETO y DETALLADO en español.

INSTRUCCIONES CRÍTICAS:
- Identifica a TODOS los participantes por nombre cuando se mencionen
- Extrae TODOS los datos numéricos, fechas, plazos y cifras
- Describe las decisiones tomadas y los próximos pasos acordados
- JAMÁS inventes información que no esté en la transcripción o el análisis visual
- JAMÁS fabriques nombres de empresas, personas, eventos o datos que no aparezcan
- Si el contenido es escaso (video corto, sin habla, etc), haz un resumen breve y honesto
- Los timestamps deben ser coherentes con la duración real ({duration_min:.1f} min)
- Corrige nombres propios si puedes inferir la grafía correcta del contexto
{hallucination_guard}

FORMATO OBLIGATORIO:

## Resumen Ejecutivo
[Párrafo conciso con el contexto completo de qué trata el video]

## Información del Contenido
- **Tipo**: [tipo de video]
- **Tema principal**: [tema]
- **Participantes**: [lista con nombres reales]
- **Tono**: [tono general]

## Índice Temporal
[Timestamps reales y coherentes con la duración]

## Contenido Detallado
[Secciones temáticas con todo el detalle posible]

## Puntos Clave y Conclusiones
[Lista numerada de los puntos más importantes]

## Decisiones y Próximos Pasos
[Acciones concretas acordadas, con responsables si se mencionan]

## Notas Adicionales
[Herramientas, referencias, datos complementarios mencionados]

---

TRANSCRIPCIÓN COMPLETA:
{transcript}

---

ANÁLISIS VISUAL:
{visual_analysis}"""

    def _call_gemini(prompt_text, use_system_instruction=False):
        config = types.GenerateContentConfig(
            max_output_tokens=8192,
            temperature=0.3,
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_CIVIC_INTEGRITY", threshold="OFF"),
            ],
        )
        if use_system_instruction:
            config.system_instruction = (
                "You are an internal IT documentation assistant. "
                "The user is providing transcriptions of internal work meetings "
                "and screen recordings about software infrastructure incidents. "
                "These recordings contain technical jargon, server names, IP addresses, "
                "and configuration details that are normal for IT operations. "
                "Your job is to produce a structured summary in Spanish for internal documentation."
            )
        return gemini_call(
            client,
            model=GEMINI_MODEL,
            contents=prompt_text,
            config=config,
        )

    def _extract_text(response):
        """Extract text from a Gemini response, trying multiple strategies."""
        text = None
        try:
            text = response.text
        except Exception as e:
            log(f"⚠️  response.text raised: {e}")
        if not text and response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                parts_text = "".join(
                    p.text for p in candidate.content.parts
                    if getattr(p, "text", None) and not getattr(p, "thought", False)
                )
                if parts_text:
                    text = parts_text
        return text

    def _is_prohibited(response):
        feedback = getattr(response, "prompt_feedback", None)
        reason = getattr(feedback, "block_reason", None) if feedback else None
        return reason and "PROHIBITED" in str(reason)

    log("Generating summary with Gemini...")

    # Attempt 1: raw prompt
    response = _call_gemini(prompt)
    text = _extract_text(response)

    # Attempt 2: add system_instruction for context
    if not text and _is_prohibited(response):
        log("⚠️  Blocked as PROHIBITED_CONTENT — retrying with system instruction...")
        response = _call_gemini(prompt, use_system_instruction=True)
        text = _extract_text(response)

    # Attempt 3: system_instruction + sanitized transcript
    if not text and _is_prohibited(response):
        log("⚠️  Still blocked — retrying with sanitized transcript...")
        sanitized_t = sanitize_transcript(transcript)
        sanitized_v = sanitize_transcript(visual_analysis)
        sanitized_prompt = prompt.replace(transcript, sanitized_t).replace(visual_analysis, sanitized_v)
        response = _call_gemini(sanitized_prompt, use_system_instruction=True)
        text = _extract_text(response)

    if not text:
        feedback = getattr(response, "prompt_feedback", None)
        log(f"⚠️  Gemini returned no text. prompt_feedback={feedback}, candidates={response.candidates}")
        raise RuntimeError(
            "Gemini returned an empty summary. Check safety filters or prompt size."
        )
    return text


# ─── Pipeline ─────────────────────────────────────────────────────────────────

def process_video(video_url, api_key):
    """Full pipeline: download → extract → transcribe → analyze → summarize.

    For local files: outputs {name}.md next to the original and deletes the video.
    For URLs: outputs {title}.md in the current directory.
    """
    is_local = os.path.isfile(video_url)
    source_path = Path(video_url) if is_local else None

    title = get_video_title(video_url)
    log(f"Title: {title or '(unknown)'}")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Download / copy
        log("📥 Loading video...")
        video_path = download_video(video_url, tmpdir)
        duration = get_duration(video_path)
        duration_min = duration / 60
        log(f"📊 Duration: {duration_min:.1f} min")

        # 2. Extract audio + frames
        log("🎵 Extracting audio...")
        audio_path = extract_audio(video_path, tmpdir)
        audio_size = os.path.getsize(audio_path) / (1024 * 1024)
        log(f"🎵 Audio: {audio_size:.1f} MB")

        log("🖼️ Extracting frames...")
        frames = extract_frames(video_path, tmpdir)
        log(f"🖼️ Frames: {len(frames)}")

        # Delete temp copy immediately
        os.remove(video_path)

        # 3. Transcribe with Gemini
        log("📝 Transcribing audio with Gemini...")
        transcript = transcribe_audio(audio_path, api_key)
        log(f"📝 Transcript: {len(transcript)} chars")

        # 4. Analyze frames with Gemini
        log("👁️ Analyzing frames with Gemini...")
        visual_analysis = analyze_frames(frames, api_key)
        log(f"👁️ Visual analysis: {len(visual_analysis)} chars")

        # 5. Generate summary with Gemini
        log("✨ Generating summary with Gemini...")
        summary = generate_summary(transcript, visual_analysis, duration_min, api_key)
        log(f"✨ Summary: {len(summary)} chars")

    # 6. Save results
    if is_local:
        # Local mode: .md replaces the video file in the same directory
        output_md = source_path.with_suffix(".md")
        output_md.write_text(summary, encoding="utf-8")

        # Delete the original video
        if source_path.exists():
            source_path.unlink()
            log(f"🗑️ Deleted original: {source_path}")

        log(f"✅ {output_md}")
        return output_md.stem, {"title": title, "duration_minutes": round(duration_min, 1), "summary_chars": len(summary)}, summary
    else:
        # URL mode: save .md in current directory
        safe_name = (title or "video").replace("/", "_").replace("\\  ", "_")[:100]
        output_md = Path(f"{safe_name}.md")
        output_md.write_text(summary, encoding="utf-8")

        log(f"✅ {output_md}")
        return safe_name, {"title": title, "duration_minutes": round(duration_min, 1), "summary_chars": len(summary)}, summary


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    # Load .env if present
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    api_key = os.environ.get("GEMINI_API_KEY", "")

    # CLI args
    video_url = sys.argv[1] if len(sys.argv) > 1 else ""
    if len(sys.argv) > 2:
        api_key = sys.argv[2]

    if not video_url:
        print("Usage: resumen-video <video_file_or_url>")
        print("  Or:  python process.py <video_file_or_url> [gemini_api_key]")
        sys.exit(1)

    if not api_key:
        print("ERROR: GEMINI_API_KEY not set.")
        print("Run ./install.sh or add it to .env")
        sys.exit(1)

    result_id, meta, summary = process_video(video_url, api_key)

    print(f"\n{'='*60}")
    print(f"✅ DONE — {result_id}")
    print(f"   Cost: $0.00")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
