# 📚 Template de Documentación LaTeX Automatizada

Bienvenido al **Template de Documentación Técnica y Guía de Usuario**. Este repositorio está diseñado para proveerte de una base profesional en **LaTeX** lista para usar, junto con un poderoso ecosistema de **Automatización mediante Inteligencia Artificial (Agent Skills)**.

El objetivo de este template es permitirte documentar cualquier sistema de software (Web, Mobile, APIs) de forma estandarizada, hermosa y rápida, delegando el trabajo repetitivo a la IA.

---

## 📦 1. Integrando el Template a tu Proyecto

Tienes dos formas principales de usar esta plantilla en tus proyectos de software:

### Opción A: Como Submódulo Git (Recomendado)
Si quieres que tu repositorio principal rastree esta documentación como una entidad separada, ve a la raíz de tu proyecto y ejecuta:
```bash
git submodule add https://github.com/tu-usuario/doc-template-latex.git docs-template
cd docs-template
```
*Esta opción es ideal porque mantienes el historial de tu código separado del historial de tu documentación.*

### Opción B: Copia Directa
Si prefieres tener todo en un mismo repositorio sin submódulos, simplemente clona este repositorio, borra la carpeta `.git` interna, y cópialo dentro de tu proyecto (ej. en una carpeta `/docs`).

---

## 🚀 2. Configuración Inicial (El paso más importante)

Antes de empezar a escribir o pedirle a la IA que documente tu sistema, necesitas "bautizar" tu proyecto. Este template es 100% dinámico y se adaptará a la identidad de tu empresa o aplicación.

> **💡 CONSEJO PRO: ¡Pídele ayuda a tu IA!**
> Si estás usando un agente (como Claude, Gemini o Cursor) en tu proyecto, no tienes que hacer esto a mano. Simplemente dile a tu agente: 
> *"Revisa mi base de código actual y ayúdame a llenar el archivo `docs-template/project.conf` con los colores de mi marca, el stack tecnológico que uso y el nombre de mi proyecto."*

1. **Abre el archivo `project.conf`** que está en la raíz de este directorio.
2. **Personaliza los valores**. El archivo está dividido en secciones muy intuitivas:
   - `[project]`: Nombre de tu software, institución y versión.
   - `[colors]`: ¡Define los colores RGB de tu marca! El template generará automáticamente entornos y estilos basados en estos colores.
   - `[stack]`: Define si tu app es React, Django, etc. Esto le ayuda a la IA a entender qué está viendo.
   - `[agent_skills]`: Define un prefijo único para tus entornos LaTeX (ej. si pones `nota`, el script creará el entorno `\begin{notamiempresa}`).

3. **Ejecuta el inicializador:**
   Una vez guardado el `project.conf`, abre tu terminal y ejecuta:
   ```bash
   python scripts/init_project.py
   ```
   *✨ ¡Magia! Este script leerá tu configuración y autogenerará los preámbulos LaTeX, los colores institucionales, el Makefile y la configuración base de los agentes de IA.*

---

## 📖 3. Escribiendo la Documentación

La estructura de carpetas de LaTeX está pensada de forma modular para que proyectos grandes no se vuelvan un desastre de código.

### Estructura de archivos
- `docs/documentacion_tecnica.tex`: El esqueleto principal del manual técnico.
- `docs/guia_usuario.tex`: El esqueleto principal del manual de usuario.
- `docs/sections/`: **¡Aquí es donde ocurre la acción!** Cada pantalla o módulo de tu sistema debe tener su propio archivo `.tex` aquí (ej. `01_login.tex`).
- `docs/images/`: Guarda todas tus capturas de pantalla aquí, organizadas en subcarpetas.

### Compilando el PDF
Necesitas tener `latexmk` y `pdflatex` instalados en tu sistema.
Para ver tus PDFs finales, entra a la carpeta `docs` y usa el comando `make`:

```bash
cd docs
make          # Compila ambos manuales
make tecnica  # Compila solo la Documentación Técnica
make guia     # Compila solo la Guía de Usuario
make clean    # Borra los archivos temporales de LaTeX
```

---

## 🤖 4. Automatización con IA (Agent Skills)

¡No tienes que escribir la documentación tú mismo! Este template incluye scripts en Python (`agent_skills/`) capaces de navegar por tu sistema web, tomar capturas de pantalla, añadirles anotaciones rojas y usar modelos como **GPT-4o o Gemini 1.5** para redactar el código LaTeX por ti.

### Preparando el entorno de la IA
1. Entra a `agent_skills/` y crea el archivo de credenciales locales (este archivo está ignorado en Git por seguridad):
   ```bash
   cd agent_skills
   touch .env.docs
   ```
2. Añade tus credenciales a `.env.docs`:
   ```env
   # Credenciales para que el bot haga login en tu app
   TEST_USER=admin@miempresa.com
   TEST_PASSWORD=secreto123

   # Elige tu IA: "gemini" o "openai"
   AI_PROVIDER=gemini
   AI_API_KEY=tu_api_key_aqui
   ```
3. Instala las dependencias de Python (preferiblemente en un entorno virtual):
   ```bash
   pip install -r requirements.txt
   ```

### 🧠 Evitando Alucinaciones: Inyección de Código (Code Context)
A veces la IA no adivina correctamente para qué sirve un botón solo viendo la captura de pantalla. ¡Para eso le pasamos el código fuente!

Abre `agent_skills/config.py` y define tus módulos. Añade la propiedad `code_sources` con las rutas a los archivos reales de tu proyecto (React, Vue, Django).

> **💡 CONSEJO PRO:**
> Nuevamente, ¡delega esto a tu IA! Puedes pedirle:
> *"Revisa las vistas de mi aplicación y genérame el diccionario `MODULES` para `agent_skills/config.py`, asegurándote de incluir en `code_sources` los componentes correctos para cada pantalla."*

```python
MODULES = [
    {
        "id": "login",
        "name": "Módulo de Autenticación",
        "url": "http://localhost:3000/login",
        "section_file": "01_login",
        "images_folder": "login",
        # La IA leerá estos archivos para entender exactamente qué hace la pantalla
        "code_sources": [
            "frontend/src/pages/Login.jsx",
            "backend/api/auth.py"
        ]
    }
]
```

### Ejecutando la automatización
Una vez configurado tu `config.py`, puedes pedirle al orquestador que documente todo:

```bash
python agent_skills/orchestrator.py --all
```
*El orquestador abrirá Chrome, navegará por tu app, leerá el código fuente, consultará a la IA y creará el archivo `.tex` terminado.*

---

## 💡 Flujo de Trabajo Recomendado
1. **Configura** `project.conf` e inicializa (`init_project.py`).
2. **Usa** un Agente de IA (Cursor, Cline, Gemini) y pásale el archivo `GEMINI.md`. Ese archivo contiene las "Instrucciones de Sistema" estrictas para que la IA sepa cómo programar en este entorno LaTeX específico.
3. **Delega** la redacción de los módulos a los scripts de `agent_skills`.
4. **Compila** con `make` y disfruta de tu documentación impecable.
