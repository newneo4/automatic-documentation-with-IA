# Agent Skills para Documentación

Este directorio contiene un conjunto de **Agent Skills** (habilidades de agente) diseñados para automatizar la generación de documentación técnica de tus proyectos de software.

Los scripts permiten a agentes de IA (o usuarios manuales) navegar por el sistema, tomar capturas de pantalla, añadir anotaciones visuales, generar descripciones con IA y producir código LaTeX listo para compilar.

## Requisitos

1. Python 3.10 o superior
2. Google Chrome instalado en el sistema local
3. (Opcional) API Key de Gemini u OpenAI si se desea generación automática de descripciones.

## Instalación

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno
source venv/bin/activate  # Linux/Mac
# o en Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

## Configuración (`.env.docs`)

El sistema utiliza un archivo de credenciales locales excluido de Git llamado `.env.docs`. 
Asegúrate de que este archivo exista en la misma carpeta que los scripts (`docs/agent_skills/`) y contenga tus credenciales:

```env
TEST_USER=tu_usuario@ejemplo.com
TEST_PASSWORD=tu_password

# Opcional: para descripciones con IA (gemini o openai)
AI_PROVIDER=gemini
AI_API_KEY=tu_api_key_aqui
```
*(No compartas ni hagas commit de este archivo)*.

## Uso del Orquestador (Recomendado)

El orquestador (`orchestrator.py`) coordina todos los skills para documentar un módulo completo de forma automática.

```bash
# Documentar un módulo específico
python orchestrator.py --module dashboard

# Documentar todos los módulos
python orchestrator.py --all

# Listar módulos disponibles
python orchestrator.py --list
```

## Uso de Skills Independientes

También puedes ejecutar cada paso del flujo por separado:

**1. Probar el login:**
```bash
python skill_01_login.py
```

**2. Tomar captura de pantalla:**
```bash
python skill_02_capture.py --module dashboard
```

**3. Añadir anotaciones rojas a una captura:**
```bash
python skill_03_annotate.py --image ../images/dashboard/dashboard.png --boxes "100,200,400,350"
```

**4. Generar descripción:**
```bash
python skill_04_describe.py --image ../images/dashboard/dashboard.png --module dashboard
```

**5. Generar bloque LaTeX (requiere el JSON de describe):**
```bash
python skill_05_latex_writer.py --description resultado.json
```

**6. Flujo completo para un módulo sin orquestador:**
```bash
python skill_06_section_builder.py --module dashboard
```
