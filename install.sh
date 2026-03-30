#!/usr/bin/env bash
set -euo pipefail

# ─── resumen-video installer ─────────────────────────────────────────────────
# Instala todo lo necesario para usar resumen-video en Linux/macOS/WSL.
# Uso: ./install.sh
# ──────────────────────────────────────────────────────────────────────────────

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "📹 Instalando resumen-video..."
echo ""

# 1. Comprobar Python 3
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 no encontrado. Instálalo primero:"
    echo "   Ubuntu/Debian: sudo apt install python3 python3-venv"
    echo "   macOS:         brew install python3"
    exit 1
fi
echo "✅ Python 3: $(python3 --version)"

# 2. Comprobar ffmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "❌ ffmpeg no encontrado. Instálalo primero:"
    echo "   Ubuntu/Debian: sudo apt install ffmpeg"
    echo "   macOS:         brew install ffmpeg"
    exit 1
fi
echo "✅ ffmpeg: $(ffmpeg -version 2>&1 | head -1)"

# 3. Crear entorno virtual e instalar dependencias
echo ""
echo "📦 Instalando dependencias Python..."
python3 -m venv "$REPO_DIR/.venv"
"$REPO_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$REPO_DIR/.venv/bin/pip" install --quiet -r "$REPO_DIR/scripts/requirements.txt"
echo "✅ Dependencias instaladas"

# 4. Configurar API key
ENV_FILE="$REPO_DIR/.env"
if [[ -f "$ENV_FILE" ]] && grep -q "GEMINI_API_KEY=." "$ENV_FILE"; then
    echo "✅ API key ya configurada en .env"
else
    echo ""
    echo "🔑 Necesitas una API key de Gemini (gratis)."
    echo ""
    echo "   1. Abre: https://aistudio.google.com/apikey"
    echo "   2. Haz click en 'Create API Key'"
    echo "   3. Copia la key (empieza por AIza...)"
    echo ""
    read -rp "   Pega tu API key aquí: " API_KEY
    if [[ -z "$API_KEY" ]]; then
        echo "⚠️  Sin API key. Puedes añadirla después en $ENV_FILE"
        echo "GEMINI_API_KEY=" > "$ENV_FILE"
    else
        echo "GEMINI_API_KEY=$API_KEY" > "$ENV_FILE"
        echo "✅ API key guardada en .env"
    fi
fi

# 5. Instalar comando resumen-video en el shell
SHELL_RC=""
if [[ -f "$HOME/.zshrc" ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ -f "$HOME/.bashrc" ]]; then
    SHELL_RC="$HOME/.bashrc"
fi

FUNC_MARKER="# resumen-video"
if [[ -n "$SHELL_RC" ]] && ! grep -q "$FUNC_MARKER" "$SHELL_RC" 2>/dev/null; then
    cat >> "$SHELL_RC" << SHELL_FUNC

# resumen-video: summarize a video file (.mp4 → .md, deletes original)
resumen-video() {
  local video="\$(realpath "\$1")"
  if [[ ! -f "\$video" ]]; then
    echo "Error: file not found — \$1" >&2
    return 1
  fi
  (source "$REPO_DIR/.venv/bin/activate" && python "$REPO_DIR/scripts/process.py" "\$video")
}
SHELL_FUNC
    echo "✅ Comando 'resumen-video' añadido a $(basename "$SHELL_RC")"
else
    if [[ -z "$SHELL_RC" ]]; then
        echo "⚠️  No se encontró .zshrc ni .bashrc. Añade manualmente la función resumen-video."
    else
        echo "✅ Comando 'resumen-video' ya existe en $(basename "$SHELL_RC")"
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ ¡Instalación completada!"
echo ""
echo "   Abre una terminal nueva y ejecuta:"
echo ""
echo "   resumen-video mi-video.mp4"
echo ""
echo "   El .mp4 se convierte en .md y se borra el original."
echo "════════════════════════════════════════════════════════════"
