# 📚 Template de Documentación LaTeX Automatizada

![LaTeX](https://img.shields.io/badge/LaTeX-47A141?style=for-the-badge&logo=LaTeX&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=Selenium&logoColor=white)
![AI Ready](https://img.shields.io/badge/AI_Ready-Gemini_|_GPT4-000000?style=for-the-badge)

Una **plantilla de arranque (Starter Boilerplate)** diseñada para generar documentación técnica y manuales de usuario profesionales en formato PDF. 

Lo que hace único a este template es su integración nativa con un ecosistema de **Agent Skills** en Python. Esto permite que agentes de Inteligencia Artificial (como Gemini, Claude o Cursor) asuman el trabajo repetitivo: navegan tu app, toman capturas de pantalla, las anotan y escriben el código LaTeX por ti.

---

## ⚡ Quick Start (De cero a PDF en 2 minutos)

La mejor manera de usar este template es tratarlo como un boilerplate y adueñarte del código. 

Abre tu terminal en la raíz de tu proyecto principal y ejecuta:

```bash
# 1. Copia el template (descarga sin el historial de git original)
npx degit newneo4/automatic-documentation-with-IA docs

# 2. Entra a la nueva carpeta
cd docs

# 3. ¡IMPORTANTE! Edita 'project.conf' con los datos de tu proyecto
# (Abre project.conf en tu editor y define tus colores institucionales y nombre)

# 4. Inicializa el proyecto para generar los estilos en base a tu configuración
python scripts/init_project.py

# 5. (Opcional) Instala las dependencias si vas a usar la IA para documentar
pip install -r agent_skills/requirements.txt

# 6. Compila la documentación base de prueba
cd docs && make
```
¡Felicidades! 🎉 Tienes un `documentacion_tecnica.pdf` compilado en tu carpeta `docs/`.

---

## 📦 ¿Qué método de instalación debo elegir?

Este repositorio es un **Template**, no una librería. Puesto que necesitarás modificar la configuración, agregar imágenes y editar archivos `.tex`, **NO recomendamos el uso de Git Submodules** para la mayoría de los casos.

| Método | Casos de Uso | Comandos |
|--------|--------------|----------|
| **Copia Independiente (Recomendado)** | Quieres la documentación dentro de tu mono-repo y planeas versionar los cambios (`.tex`, imágenes) junto con tu código fuente. No genera conflictos de submódulos sucios. | `npx degit newneo4/automatic-documentation-with-IA docs` <br> *(o clonar y borrar `.git`)* |
| **Repositorio Separado** | El equipo de documentación es distinto al de desarrollo. Quieres mantener el historial de la documentación completamente aislado. | Dale al botón **"Use this template"** en GitHub. |
| **Git Submodule (Avanzado)** | Tienes experiencia avanzada en Git, deseas recibir actualizaciones upstream (commits del creador del template) y sabes cómo lidiar con cabezas desacopladas (`detached HEAD`). | `git submodule add https://github.com/newneo4/automatic-documentation-with-IA.git docs` |

---

## 🚀 Configuración Inicial

Este template es 100% dinámico. Antes de escribir una sola línea, necesitas "bautizar" tu proyecto para que los colores institucionales y los preámbulos se generen solos.

> **💡 CONSEJO DX (Developer Experience): ¡No lo hagas a mano!**
> Si estás usando un agente de IA en tu IDE (como Cursor o Cline), simplemente dile:
> *"Revisa mi base de código actual y ayúdame a llenar el archivo `docs/project.conf` con los colores exactos de mi frontend, el stack tecnológico que uso y el nombre formal de mi proyecto."*

1. Edita el archivo `project.conf`.
2. Ejecuta el inicializador en la raíz de tu carpeta de documentación:
   ```bash
   python scripts/init_project.py
   ```
   *Esto autogenerará paletas de colores LaTeX personalizadas, Makefiles y configurará el entorno de la IA.*

---

## 🤖 Magia Negra: Automatización con IA

La carpeta `agent_skills/` contiene scripts de automatización con Selenium. En lugar de sacar capturas a mano y redactar texto aburrido, la IA lo hará por ti.

### 1. Prepara las credenciales locales
Crea un archivo `.env.docs` en la carpeta `agent_skills/` (este archivo está ignorado por Git por seguridad):
```env
# Usuario de prueba para que el bot navegue tu sistema
TEST_USER=admin@miempresa.com
TEST_PASSWORD=secreto123

# LLM a utilizar
AI_PROVIDER=gemini # o openai
AI_API_KEY=tu_api_key
```

### 2. Evita alucinaciones (Inyección de Contexto)
Para que la IA no invente descripciones viendo solo una foto, puedes inyectarle tu código fuente. Abre `agent_skills/config.py` y añade la propiedad `code_sources`:

```python
MODULES = [
    {
        "id": "login",
        "url": "http://localhost:3000/login",
        "section_file": "01_login",
        # ¡El agente leerá estos archivos para describir el frontend con precisión milimétrica!
        "code_sources": [
            "frontend/src/pages/Login.jsx",
            "backend/api/auth.py"
        ]
    }
]
```

### 3. Ejecuta el Orquestador
Instala los requirements y pon a trabajar al bot:
```bash
pip install -r agent_skills/requirements.txt
python agent_skills/orchestrator.py --all
```
El agente abrirá Chrome, tomará capturas, dibujará rectángulos rojos sobre los botones, invocará al LLM y te devolverá un archivo `.tex` listo para compilar.

---

## 📖 Arquitectura y Compilación

La estructura modular de LaTeX vive en `docs/`:
- `docs/*.tex`: Los esqueletos principales.
- `docs/sections/*.tex`: El contenido real (tus módulos).
- `docs/images/`: Guarda aquí las capturas generadas.

Para compilar, asegúrate de tener `latexmk` y `pdflatex` instalados.
```bash
cd docs
make          # Compila toda la suite
make tecnica  # Compila la Documentación Técnica
make guia     # Compila la Guía de Usuario
make clean    # Limpia basura de LaTeX (.aux, .log, etc)
```

---

## ❓ FAQ & Buenas Prácticas

**¿Cómo le enseño a mi IA a programar en LaTeX bajo las reglas de este template?**
Aliméntale el archivo `GEMINI.md` a tu agente. Ese archivo contiene el "System Prompt" maestro con todas las reglas institucionales, colores y macros estandarizadas del template.

**¿Qué pasa si mi sistema no tiene Interfaz Gráfica (ej. una API)?**
Puedes ejecutar la documentación de código (usando `code_sources`) saltándote el paso de captura gráfica de Selenium si así lo requieres, construyendo las secciones manualmente con ayuda del agente.
