"""
Configuración compartida para las Agent Skills del sistema de documentación.
Generado desde project.conf
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Configuración base del frontend (reemplazada por init_project.py)
BASE_URL = "{{BASE_URL}}"
LOGIN_URL = "{{LOGIN_URL}}"

# Configuración de Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_PATH = BASE_DIR / "docs"
IMAGES_PATH = DOCS_PATH / "images"
SECTIONS_PATH = DOCS_PATH / "sections"
SKILLS_PATH = Path(__file__).parent

# Entornos LaTeX
ENV_PREFIX = "{{ENV_PREFIX}}"
LATEX_IMAGE_WIDTH = "0.85"
LATEX_FIGURE_POSITION = "H"

# Dimensiones y Captura
SCREENSHOT_WIDTH = 1280
SCREENSHOT_HEIGHT = 720
SCREENSHOT_WAIT = 1.5
SCREENSHOT_FORMAT = "png"

# Logging
LOG_LEVEL = "INFO"

# Color y grosor de anotaciones
COLOR_ANNOTATION = (255, 0, 0)
ANNOTATION_LINE_WIDTH = 3

# Cargar credenciales desde .env
env_path = BASE_DIR / "agent_skills" / ".env.docs"
load_dotenv(dotenv_path=env_path)

USERNAME = os.getenv("TEST_USER", "")
PASSWORD = os.getenv("TEST_PASSWORD", "")

# (Opcional) Define aquí módulos dinámicamente o expórtalos a un archivo de configuración separado
MODULES = [
    {
        "id": "login",
        "name": "Módulo de Autenticación",
        "url": f"{BASE_URL}{LOGIN_URL}",
        "section_file": "01_login",
        "images_folder": "login",
        "wait_for_selector": "form button[type='submit']", # (Opcional) Esperar a que este selector CSS exista (útil para SPAs)
        "code_sources": [
            "frontend/src/pages/Login.vue",
            "backend/api/views/auth.py"
        ]
    }
]

MODULES_BY_ID = {m["id"]: m for id, m in MODULES.items()} if isinstance(MODULES, dict) else {m["id"]: m for m in MODULES}

