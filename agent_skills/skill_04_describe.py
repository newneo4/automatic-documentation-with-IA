"""
skill_04_describe.py — Generación automática de descripciones para capturas
============================================================================
Analiza una captura de pantalla y genera el texto de documentación:
título de sección, descripción de la pantalla, lista de elementos UI,
caption para la figura LaTeX y label sugerido.

Modo de funcionamiento:
- Si AI_PROVIDER está configurado en .env.docs, usa la API correspondiente.
- Si AI_PROVIDER está vacío, genera una plantilla para completar manualmente.

Uso independiente:
    python skill_04_describe.py --image images/dashboard/dashboard.png \
        --module dashboard

Cuando se importa:
    describer = ScreenDescriber()
    result = describer.describe(image_path, module_id="dashboard")
"""

import base64
import json
import logging
import sys
import argparse
import re
from pathlib import Path
from typing import Optional
import config

sys.path.insert(0, str(Path(__file__).parent))

log = logging.getLogger("skill_04_describe")


class ScreenDescriber:
    """Genera descripciones en español formal para capturas de pantalla."""

    # Prompt del sistema — define el estilo formal requerido
    SYSTEM_PROMPT = """Eres un redactor técnico especializado en documentación de software universitario.
Tu tarea es describir capturas de pantalla del sistema de software que estamos documentando.

REGLAS:
1. Redactar en ESPAÑOL FORMAL, tercera persona, estilo técnico-académico.
2. El texto irá en un documento LaTeX profesional tipo manual de usuario/documentación técnica.
3. Ser específico: nombrar exactamente los botones, campos, tablas y secciones visibles.
4. Los nombres de botones y campos van en NEGRITAS en LaTeX (\\textbf{}).
5. Longitud: descripción de 2-4 oraciones, caption de 1 oración concisa.
6. NO inventar funcionalidades que no se vean en la captura.
7. Responder ÚNICAMENTE en formato JSON (sin markdown, sin bloques de código).
"""

    USER_PROMPT_TEMPLATE = """Analiza esta captura de pantalla del módulo "{module_name}".

Proporciona la siguiente información en formato JSON:
{{
  "titulo_seccion": "Título corto para la \\\\subsection{{}} de LaTeX (máx 60 caracteres)",
  "descripcion": "2-4 oraciones describiendo qué muestra la pantalla, qué hace el usuario aquí y los elementos principales visibles. Usar \\\\textbf{{}} para nombres de botones y campos.",
  "elementos_ui": ["Lista de elementos UI visibles: botones, formularios, tablas, filtros, etc."],
  "caption": "Una oración descriptiva para el \\\\caption{{}} de la figura LaTeX. Menciona el módulo y qué muestra.",
  "label": "Identificador LaTeX para \\\\label{{fig:...}} en kebab-case-sin-espacios",
  "notas_agente": "Observaciones adicionales relevantes para la documentación (puede estar vacío)"
}}

{code_context}"""

    def __init__(self):
        self.provider = (config.AI_PROVIDER or "").strip().lower()
        self.api_key = (config.AI_API_KEY or "").strip()

    def _image_to_base64(self, image_path: str) -> str:
        """Convierte una imagen a base64 para enviarla a la API."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _get_code_context(self, code_sources: list) -> str:
        """Lee y concatena el código fuente para inyectarlo en el prompt."""
        if not code_sources:
            return ""
        
        context_parts = [
            "\\nAdicionalmente, aquí tienes el CÓDIGO FUENTE subyacente de la vista para que tus descripciones sean técnicamente precisas.",
            "Usa este código para identificar el nombre exacto de los botones, campos de formularios y componentes clave:\\n"
        ]
        
        for rel_path in code_sources:
            full_path = Path(__file__).parent.parent.parent / rel_path
            if full_path.exists():
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Truncar si es exageradamente largo (max ~15k chars por archivo)
                        if len(content) > 15000:
                            content = content[:15000] + "\\n...[TRUNCADO]..."
                        context_parts.append(f"--- ARCHIVO: {rel_path} ---\\n{content}\\n{'-'*40}\\n")
                except Exception as e:
                    log.warning(f"No se pudo leer el archivo fuente {full_path}: {e}")
            else:
                log.warning(f"El archivo fuente {full_path} no existe.")
                
        return "\\n".join(context_parts)

    def _call_gemini(self, image_path: str, module_name: str, extra_data: dict = None) -> dict:
        """Llama a la API de Gemini con la imagen y el prompt."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            import PIL.Image
            image = PIL.Image.open(image_path)
            code_sources = extra_data.get("code_sources", []) if extra_data else []
            code_context = self._get_code_context(code_sources)
            prompt = self.USER_PROMPT_TEMPLATE.format(
                module_name=module_name,
                code_context=code_context
            )
            response = model.generate_content(
                [self.SYSTEM_PROMPT + "\n\n" + prompt, image]
            )
            return self._parse_response(response.text)
        except Exception as e:
            log.error(f"Error llamando a Gemini: {e}")
            return self._generate_template(module_name, module_name, image_path, extra_data)

    def _call_openai(self, image_path: str, module_name: str, extra_data: dict = None) -> dict:
        """Llama a la API de OpenAI GPT-4o con la imagen."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            b64 = self._image_to_base64(image_path)
            code_sources = extra_data.get("code_sources", []) if extra_data else []
            code_context = self._get_code_context(code_sources)
            prompt = self.USER_PROMPT_TEMPLATE.format(
                module_name=module_name,
                code_context=code_context
            )

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url",
                         "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    ]},
                ],
                response_format={"type": "json_object"},
                max_tokens=1000,
            )
            return self._parse_response(response.choices[0].message.content)
        except Exception as e:
            log.error(f"Error llamando a OpenAI: {e}")
            return self._generate_template(module_name, module_name, image_path, extra_data)

    def _parse_response(self, text: str) -> dict:
        """Extrae el JSON de la respuesta del modelo."""
        # Limpiar posibles bloques de markdown
        text = re.sub(r"```(?:json)?", "", text).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            log.warning("Respuesta no es JSON válido. Retornando como texto.")
            return {
                "titulo_seccion": "Sin título",
                "descripcion": text,
                "elementos_ui": [],
                "caption": "Captura de pantalla del sistema.",
                "label": "fig-sin-label",
                "notas_agente": "Respuesta no estructurada de la IA.",
            }

    def _generate_template(self, module_id: str, module_name: str, image_path: str, extra_data: dict = None) -> dict:
        """
        Genera una descripción estática o basada en el código Vue cuando no hay IA configurada.
        """
        label = module_id.replace("_", "-")
        caption = f"Captura de pantalla del módulo {module_name}."
        notas_agente = "Plantilla generada estáticamente (Sin IA conectada)."
        
        return {
            "titulo_seccion": f"Módulo {module_name}",
            "descripcion": f"Esta pantalla muestra el módulo \\textbf{{{module_name}}}. Permite gestionar la información principal y acceder a las opciones de configuración.",
            "elementos_ui": [
                "\\textbf{Panel principal}",
                "\\textbf{Opciones de navegación}",
                "\\textbf{Botones de acción}"
            ],
            "caption": caption,
            "label": f"fig-{label}-principal",
            "notas_agente": notas_agente,
        }

    def describe(
        self,
        image_path: str,
        module_id: str = "",
        module_name: str = "",
        extra_data: dict = None
    ) -> dict:
        """
        Genera descripción para una captura de pantalla.

        Args:
            image_path: Ruta a la imagen
            module_id: ID del módulo (para label y template)
            module_name: Nombre del módulo en español

        Returns:
            dict con: titulo_seccion, descripcion, elementos_ui, caption, label, notas_agente
        """
        if not module_name and module_id:
            mod = config.MODULES_BY_ID.get(module_id, {})
            module_name = mod.get("name", module_id)

        log.info(f"Generando descripción para: {module_name or image_path}")

        if self.provider == "gemini" and self.api_key:
            result = self._call_gemini(image_path, module_name)
        elif self.provider == "openai" and self.api_key:
            result = self._call_openai(image_path, module_name)
        else:
            log.info("Sin proveedor de IA configurado. Generando plantilla manual.")
            result = self._generate_template(module_id, module_name, image_path, extra_data)

        result["image_path"] = image_path
        result["module_id"] = module_id
        result["module_name"] = module_name
        return result


# ============================================================
# Ejecución independiente
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill 04 — Generación de descripciones")
    parser.add_argument("--image", required=True, help="Ruta a la imagen a describir")
    parser.add_argument("--module", default="",
        help="ID del módulo (ej: dashboard, semillero)")
    args = parser.parse_args()

    describer = ScreenDescriber()
    result = describer.describe(args.image, module_id=args.module)

    print("\n" + "=" * 60)
    print("  SKILL 04: Descripción generada")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
