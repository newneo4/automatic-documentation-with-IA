# Template de Documentación LaTeX Automatizada

Este repositorio es una plantilla reutilizable para generar documentación técnica y manuales de usuario profesionales en formato PDF mediante LaTeX, con soporte para automatización mediante agentes de IA (Gemini/Claude).

## ¿Cómo utilizar este template?

Existen dos formas principales de integrar este template a tu proyecto:

### Opción A: Clonar y copiar
Si deseas mantener la documentación completamente separada o integrarla directamente en tu repositorio copiando los archivos:

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tu-usuario/doc-template-latex.git docs-temporales
   cd docs-temporales
   ```
2. Modifica el archivo `project.conf` con los datos de tu proyecto.
3. Ejecuta el inicializador:
   ```bash
   python scripts/init_project.py
   ```
4. Copia las carpetas `docs` y `agent_skills` (si las necesitas) a tu proyecto principal.

### Opción B: Como Submódulo (Recomendado)
Si quieres que tu repositorio principal rastree esta documentación como una entidad separada:

1. Ve a la raíz de tu proyecto principal y añade el submódulo:
   ```bash
   git submodule add https://github.com/tu-usuario/doc-template-latex.git docs-template
   ```
2. Ingresa a la carpeta `docs-template`.
3. Edita el archivo `project.conf` con los detalles de tu nuevo proyecto.
4. Ejecuta `python scripts/init_project.py`
5. Ahora puedes empezar a generar secciones `.tex` dentro de `docs-template/docs/sections/`.

## Compilación

Para compilar los documentos PDF, asegúrate de tener `latexmk` instalado.
Dirígete a la carpeta `docs` y ejecuta:

```bash
make          # Compila todos los manuales
make tecnica  # Compila solo la Documentación Técnica
make guia     # Compila solo la Guía de Usuario
make clean    # Limpia archivos temporales
```

## Automatización con IA (Agent Skills)

Si cuentas con herramientas agenticas de IA (Gemini, Claude, Cursor, Codeium):

1. Verifica el archivo `GEMINI.md` e inclúyelo en el contexto de tu agente.
2. Copia `.env.docs` en la carpeta `agent_skills` y agrega tus credenciales si deseas que la IA tome capturas automáticamente con Selenium y las describa usando GPT-4o / Gemini.
3. **Inyección de Código Fuente**: Para evitar que la IA "alucine" o interprete mal una pantalla, puedes indicarle qué archivos componen la vista. Modifica `MODULES` en `agent_skills/config.py` agregando la propiedad `code_sources`:
   ```python
   "code_sources": [
       "frontend/src/pages/Login.jsx",
       "backend/api/auth.py"
   ]
   ```
   *La IA leerá el código fuente real (React, Vue, HTML, Django, etc.) para inferir el nombre exacto de los botones, formularios y tablas.*
4. El agente de IA se encargará de crear y ensamblar los archivos `.tex` siguiendo las reglas del template.
