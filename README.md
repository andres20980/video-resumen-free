# resumen-video

Convierte cualquier vídeo en un resumen `.md` detallado con IA. **Gratis. Un solo comando.**

```
resumen-video reunion.mp4
```

Resultado: `reunion.md` aparece donde estaba el vídeo. El `.mp4` se borra automáticamente.

---

## Instalación (2 minutos)

### Requisitos previos

Necesitas **Python 3** y **ffmpeg** instalados. Si no los tienes:

```bash
# Ubuntu/Debian/WSL
sudo apt install python3 python3-venv ffmpeg

# macOS
brew install python3 ffmpeg
```

### Instalar

```bash
git clone https://github.com/andres20980/video-resumen-free.git
cd video-resumen-free
./install.sh
```

El instalador te pedirá una **API key de Gemini** (gratis, sin tarjeta):

1. Abre https://aistudio.google.com/apikey
2. Click en **"Create API Key"**
3. Copia la key y pégala cuando te la pida

Eso es todo. Abre una terminal nueva y ya puedes usar `resumen-video`.

---

## Uso

```bash
# Resumir un vídeo local (reemplaza .mp4 por .md)
resumen-video grabacion.mp4

# Funciona con cualquier formato
resumen-video reunion.mkv
resumen-video WhatsApp\ Video\ 2026-03-30.mp4

# También con URLs de YouTube, Vimeo, etc.
resumen-video "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### ¿Qué hace exactamente?

1. Extrae el audio y los frames del vídeo
2. Transcribe el audio con Gemini (gratis)
3. Analiza los frames con Gemini Vision (gratis)
4. Genera un resumen detallado en español cruzando ambas fuentes
5. Guarda el `.md` donde estaba el vídeo y borra el original

### Ejemplo de salida

Un vídeo de 30 min de una reunión produce un `.md` con:
- Resumen ejecutivo
- Participantes identificados por nombre
- Índice temporal con timestamps
- Contenido detallado por secciones
- Puntos clave y conclusiones
- Decisiones y próximos pasos

---

## Stack

| Componente | Herramienta | Coste |
|---|---|---|
| Descarga URLs | yt-dlp | $0.00 |
| Extracción audio/frames | ffmpeg | $0.00 |
| Transcripción | Gemini 2.5 Flash | $0.00 |
| Análisis visual | Gemini 2.5 Flash | $0.00 |
| Resumen | Gemini 2.5 Flash | $0.00 |
| **TOTAL** | | **$0.00** |

## Límites del free tier de Gemini

- ~500 peticiones/día, 1M tokens/día
- En la práctica: **~8 vídeos largos (30 min) al día**
- Sin tarjeta de crédito, sin caducidad

## Licencia

MIT
