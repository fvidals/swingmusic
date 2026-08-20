#!/usr/bin/env python3
"""
SwingMeta Local Runner
Inicia o servidor backend do SwingMeta para desenvolvimento ou uso local.
"""
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = (Path(__file__).parent / "backend").resolve()
sys.path.insert(0, str(backend_dir))

from app import app
from config import settings

if __name__ == "__main__":
    print("=" * 60)
    print(" 🎵 SwingMeta - Side-load Metadata & Image Editor")
    print("=" * 60)
    print(f" • Porta: {settings.PORT}")
    print(f" • Diretório de Config: {settings.resolved_config_dir}")
    print(f" • Diretório de Músicas: {settings.MUSIC_DIR}")
    print(f" • Acesse: http://localhost:{settings.PORT}")
    print("=" * 60)
    app.run(host=settings.HOST, port=settings.PORT, debug=True)
