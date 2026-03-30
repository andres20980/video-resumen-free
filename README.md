# 📹 Video Resumen Free

Resúmenes exhaustivos de video con IA — **100% gratuito**.

## ¿Qué es?

Una pipeline que toma cualquier URL de video (YouTube, Vimeo, Google Drive...) y genera un resumen completo y detallado usando inteligencia artificial. Sin coste alguno.

## Stack

| Componente | Herramienta | Coste |
|---|---|---|
| Descarga | yt-dlp (open source) | $0.00 |
| Extracción | ffmpeg (open source) | $0.00 |
| Transcripción | Gemini 2.5 Flash (free tier) | $0.00 |
| Análisis visual | Gemini 2.5 Flash (free tier) | $0.00 |
| Resumen | Gemini 2.5 Flash (free tier) | $0.00 |
| Procesamiento | GitHub Actions (2000 min/mes gratis) | $0.00 |
| Frontend | GitHub Pages | $0.00 |
| **TOTAL** | | **$0.00** |

## ¿Cómo usarlo?

### Opción 1: Crear un Issue (recomendado)
1. Ve a [Issues → New Issue](../../issues/new?template=summarize.yml)
2. Selecciona "📹 Resumir Video"
3. Pega la URL del video
4. GitHub Actions procesará automáticamente y publicará el resumen como comentario

### Opción 2: Ejecutar manualmente
1. Ve a [Actions](../../actions) → "📹 Resumir Video"
2. Click "Run workflow"
3. Introduce la URL del video

### Opción 3: Uso local
```bash
pip install -r scripts/requirements.txt
export GEMINI_API_KEY=tu-api-key
python scripts/process.py "https://www.youtube.com/watch?v=..."
```

## Resultados

Los resúmenes se publican automáticamente en **GitHub Pages**: [ver sitio](../../deployments)

## Límites del free tier

- **Gemini**: ~500 requests/día, 1M tokens/día → ~8 videos/día
- **GitHub Actions**: 2000 minutos/mes → ~200 videos/mes (estimando ~10 min/video)
- **GitHub Pages**: 1GB de almacenamiento

## Setup

1. Fork este repositorio
2. Añade el secret `GEMINI_API_KEY` en Settings → Secrets → Actions
   - Consigue una API key gratis en [Google AI Studio](https://aistudio.google.com/apikey)
3. Habilita GitHub Pages en Settings → Pages → Source: `Deploy from a branch` → Branch: `main`, folder: `/docs`
4. ¡Listo! Crea un Issue o ejecuta el workflow manualmente

## Calidad

Pipeline comparada con soluciones de pago:

| Modelo | Coste/video | Calidad |
|---|---|---|
| GPT-4o-mini (OpenAI) | ~$0.20 | ⭐⭐⭐ |
| GPT-4o (OpenAI) | ~$0.23 | ⭐⭐⭐⭐ |
| **Gemini 2.5 Flash (este proyecto)** | **$0.00** | **⭐⭐⭐⭐⭐** |

Gemini 2.5 Flash iguala o supera a GPT-4o en transcripción, análisis visual y generación de resúmenes, especialmente en español.
