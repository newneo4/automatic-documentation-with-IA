import os
from pathlib import Path
import config
from utils.logger import log

class PromptBuilder:
    def __init__(self):
        self.prompts_dir = config.DOCS_PATH / "agent_prompts"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def _get_code_context(self, code_sources: list) -> str:
        """Lee y concatena el código fuente para inyectarlo en el prompt."""
        if not code_sources:
            return ""
        
        context_parts = [
            "\n## Contexto de Código Fuente\n",
            "Aquí tienes el código fuente subyacente de la vista para que tus descripciones sean técnicamente precisas.",
            "Usa este código para identificar el nombre exacto de los botones, campos y componentes clave:\n"
        ]
        
        for rel_path in code_sources:
            full_path = config.BASE_DIR.parent / rel_path
            if full_path.exists():
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if len(content) > 15000:
                            content = content[:15000] + "\n...[TRUNCADO]..."
                        context_parts.append(f"### Archivo: `{rel_path}`\n```\n{content}\n```\n")
                except Exception as e:
                    log.warning(f"No se pudo leer el archivo fuente {full_path}: {e}")
            else:
                log.warning(f"El archivo fuente {full_path} no existe.")
                
        return "\n".join(context_parts)

    def build_prompt(self, module_name: str, section_file: str, image_relative_path: str, code_sources: list) -> str:
        """Construye y guarda el prompt en markdown."""
        prompt_path = self.prompts_dir / f"{section_file}_prompt.md"
        
        code_context = self._get_code_context(code_sources)
        
        prompt_content = f"""# Tarea de Documentación: {module_name}

Eres un Technical Writer experto en LaTeX. Tu tarea es redactar la sección de documentación para el módulo "{module_name}".

## Instrucciones
1. Analiza la captura de pantalla proporcionada en: `docs/{image_relative_path}`
2. Lee el código fuente adjunto para entender el funcionamiento técnico.
3. Genera un archivo LaTeX válido y guárdalo exactamente en: `docs/sections/{section_file}.tex`

## Requisitos del Código LaTeX
El archivo debe contener **únicamente** código LaTeX válido (sin bloques ```latex).
Usa esta estructura base:

% ===================================================
% SECCIÓN: {module_name}
% ===================================================
\\section{{{module_name}}}

\\begin{{figure}}[H]
  \\centering
  \\includegraphics[width=0.85\\textwidth, frame]{{{image_relative_path}}}
  \\caption{{Descripción de lo que muestra la captura en el módulo {module_name}.}}
  \\label{{fig:{section_file}}}
\\end{{figure}}

% Aquí redacta una descripción de 2 a 4 párrafos sobre:
% - Qué hace esta pantalla.
% - Qué acciones puede realizar el usuario.
% - Menciona los botones principales en \\textbf{{Negrita}}.

{code_context}

---
**Por favor, procede a generar el archivo `docs/sections/{section_file}.tex` ahora mismo.**
"""
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(prompt_content)
            
        log.info(f"  📝 Prompt generado en: {prompt_path.relative_to(config.BASE_DIR)}")
        return str(prompt_path)
