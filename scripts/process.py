#!/usr/bin/env python3
"""Video Resumen Free — 100% free video summarization.

Pipeline: yt-dlp (download) → ffmpeg (extract) → Gemini 2.5 Flash (transcribe + analyze + summarize)
Cost: $0.00 — everything runs on Gemini free tier + GitHub Actions free tier.
"""

import os
import sys
import json
import subprocess
import tempfile
import re
import glob
import time
import io
from pathlib import Path
from datetime import datetime, timezone

from google import genai
from google.genai import types
from PIL import Image

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


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
    """Get video title via yt-dlp (best effort)."""
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

def get_client(api_key):
    return genai.Client(api_key=api_key)


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
    )
    response = client.models.generate_content(
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

    prompt = (
        "Analiza estas imágenes extraídas de un video. Para cada imagen relevante:\n"
        "1. Describe qué se ve (personas, presentaciones, documentos, pantallas compartidas)\n"
        "2. Transcribe TODO el texto visible en pantalla literalmente\n"
        "3. Identifica logos, diagramas, datos numéricos, gráficos\n"
        "4. Agrupa imágenes similares para evitar repetición\n\n"
        "Sé exhaustivo con el texto en pantalla — transcribe literalmente todo lo legible."
    )
    parts = [prompt]

    for fp in frame_paths:
        img = Image.open(fp)
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        parts.append(types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"))

    log(f"Analyzing {len(frame_paths)} frames with Gemini vision...")
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=parts,
        config=types.GenerateContentConfig(
            max_output_tokens=4096,
            temperature=0.2,
        ),
    )
    return response.text


def generate_summary(transcript, visual_analysis, duration_min, api_key):
    """Generate comprehensive summary using Gemini (free)."""
    client = get_client(api_key)

    prompt = f"""Eres un experto en generar resúmenes exhaustivos de videos.
A partir de la transcripción y el análisis visual de un video de {duration_min:.1f} minutos,
genera un resumen COMPLETO y DETALLADO en español.

INSTRUCCIONES CRÍTICAS:
- Identifica a TODOS los participantes por nombre cuando se mencionen
- Extrae TODOS los datos numéricos, fechas, plazos y cifras
- Describe las decisiones tomadas y los próximos pasos acordados
- NO inventes información que no esté en la transcripción
- Los timestamps deben ser coherentes con la duración real ({duration_min:.1f} min)
- Corrige nombres propios si puedes inferir la grafía correcta del contexto

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

    log("Generating summary with Gemini...")
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=8192,
            temperature=0.3,
        ),
    )
    return response.text


# ─── Pipeline ─────────────────────────────────────────────────────────────────

def process_video(video_url, api_key, results_dir="docs/data"):
    """Full pipeline: download → extract → transcribe → analyze → summarize."""
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    title = get_video_title(video_url)
    log(f"Title: {title or '(unknown)'}")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Download
        log("📥 Downloading video...")
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

        # Delete video to free disk space
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
    result_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    (results_dir / f"{result_id}.md").write_text(summary, encoding="utf-8")
    (results_dir / f"{result_id}_transcript.txt").write_text(transcript, encoding="utf-8")

    meta = {
        "id": result_id,
        "title": title or video_url,
        "url": video_url,
        "duration_minutes": round(duration_min, 1),
        "transcript_chars": len(transcript),
        "summary_chars": len(summary),
        "frames_analyzed": len(frames),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cost_usd": 0.00,
        "models": {
            "transcription": f"gemini/{GEMINI_MODEL}",
            "vision": f"gemini/{GEMINI_MODEL}",
            "summary": f"gemini/{GEMINI_MODEL}",
        },
    }
    (results_dir / f"{result_id}.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Update index
    index_path = results_dir / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    index.insert(0, meta)
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    log(f"✅ Results saved: docs/data/{result_id}.*")
    return result_id, meta, summary


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    # Get config from env (GitHub Actions) or CLI args (local)
    video_url = os.environ.get("VIDEO_URL", "")
    issue_body = os.environ.get("ISSUE_BODY", "")
    api_key = os.environ.get("GEMINI_API_KEY", "")

    # CLI override
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
    if len(sys.argv) > 2:
        api_key = sys.argv[2]

    # Extract URL from issue body if not provided directly
    if not video_url and issue_body:
        urls = re.findall(r'https?://[^\s\)\"'"'"']+', issue_body)
        if urls:
            video_url = urls[0]

    if not video_url:
        print("Usage: python process.py <video_url> [gemini_api_key]")
        print("  Or set VIDEO_URL and GEMINI_API_KEY env vars")
        sys.exit(1)

    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    result_id, meta, summary = process_video(video_url, api_key)

    # Write GitHub Actions comment file
    issue_number = os.environ.get("ISSUE_NUMBER", "")
    if issue_number:
        comment = f"""## 📹 Resumen generado

| | |
|---|---|
| **Video** | [{meta['title']}]({meta['url']}) |
| **Duración** | {meta['duration_minutes']} min |
| **Coste** | $0.00 💚 |
| **Modelos** | Gemini 2.5 Flash (transcripción + visión + resumen) |

---

{summary}

---

<details>
<summary>📊 Detalles técnicos</summary>

- Transcripción: {meta['transcript_chars']} caracteres (Gemini)
- Análisis visual: {meta['frames_analyzed']} frames (Gemini)
- Resumen: {meta['summary_chars']} caracteres (Gemini)
- Resultado: docs/data/{result_id}.md

</details>
"""
        Path("comment.md").write_text(comment, encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"✅ DONE — Result ID: {result_id}")
    print(f"   Summary: docs/data/{result_id}.md")
    print(f"   Transcript: docs/data/{result_id}_transcript.txt")
    print(f"   Cost: $0.00")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
