"""
skill_05_latex_writer.py — Generación de bloques LaTeX para la documentación
==================================================================================
Convierte la metadata de capturas y descripciones en código LaTeX
listo para insertar en los archivos de secciones.

Uso independiente:
    python skill_05_latex_writer.py --description resultado_describe.json

Cuando se importa:
    writer = LatexWriter()
    block = writer.figure_block(capture_result, description_result)
    block = writer.subsection_block(description_result)
    block = writer.step_block(step_number, description, capture_result)
"""

import json
import logging
import sys
import argparse
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
import config

log = logging.getLogger("skill_05_latex_writer")


class LatexWriter:
    """Genera bloques LaTeX para la documentación técnica."""

    def __init__(self):
        self.env_prefix = getattr(config, "ENV_PREFIX", "nota")

    def _escape(self, text: str) -> str:
        """Escapa caracteres especiales de LaTeX (básico)."""
        # No escapar los ya insertados (\textbf{}, etc.)
        if not text:
            return ""
        # Solo escapar & y % fuera de comandos LaTeX
        result = text.replace("%", "\\%")
        # No reemplazar & dentro de tabular/etc. — el usuario lo maneja manualmente
        return result

    def figure_block(
        self,
        capture: dict,
        description: dict,
        width: str = None,
        annotated: bool = False,
    ) -> str:
        """
        Genera el entorno figure[H] completo con imagen, caption y label.

        Args:
            capture: dict retornado por skill_02_capture
            description: dict retornado por skill_04_describe
            width: Fracción de textwidth (ej: "0.85")
            annotated: Si True, usa la imagen con sufijo -anotado

        Returns:
            Bloque LaTeX como string
        """
        width = width or config.LATEX_IMAGE_WIDTH
        position = config.LATEX_FIGURE_POSITION

        # Determinar la ruta relativa a la imagen
        img_path = capture.get("relative_path", "images/general/placeholder.png")
        if annotated:
            p = Path(img_path)
            img_path = str(p.parent / f"{p.stem}-anotado{p.suffix}")

        caption = self._escape(description.get("caption", "Captura de pantalla del sistema DRII."))
        label = description.get("label", "fig-sin-label")

        return f"""\\begin{{figure}}[{position}]
  \\centering
  \\includegraphics[width={width}\\textwidth, frame]{{{img_path}}}
  \\caption{{{caption}}}
  \\label{{{label}}}
\\end{{figure}}
"""

    def subsection_block(self, description: dict, include_figure: bool = True,
                         capture: dict = None) -> str:
        """
        Genera una subsección completa: título, descripción y opcionalmente la figura.

        Args:
            description: dict de skill_04_describe
            include_figure: Si True, incluye el bloque figure
            capture: Necesario si include_figure=True
        """
        titulo = description.get("titulo_seccion", "[Título de sección]")
        desc_text = description.get("descripcion", "[Descripción pendiente]")
        elementos = description.get("elementos_ui", [])
        notas = description.get("notas_agente", "")

        lines = [f"\\subsection{{{titulo}}}\n"]
        lines.append(f"{desc_text}\n")

        if elementos:
            lines.append("\nLos principales elementos disponibles en esta pantalla son:\n")
            lines.append("\\begin{itemize}")
            for elem in elementos:
                lines.append(f"  \\item {self._escape(elem)}")
            lines.append("\\end{itemize}\n")

        if include_figure and capture:
            lines.append(self.figure_block(capture, description))

        if notas and "[COMPLETAR" not in notas:
            env_nota = f"nota{self.env_prefix}"
            lines.append(f"\\begin{{{env_nota}}}\n  {self._escape(notas)}\n\\end{{{env_nota}}}\n")

        return "\n".join(lines)

    def section_header(self, module: dict) -> str:
        """
        Genera el comentario de cabecera y \\section para un módulo.

        Args:
            module: dict de config.MODULES (con id, name, url)
        """
        from datetime import date
        today = date.today().strftime("%Y-%m-%d")
        name = module["name"]
        url = module.get("url", "")
        section_file = module.get("section_file", "XX_modulo")

        return f"""% ===================================================
% SECCIÓN: {name}
% URL: {url}
% Última actualización: {today}
% ===================================================
\\section{{{name}}}

"""

    def step_block(
        self,
        step_number: int,
        description_text: str,
        capture: Optional[dict] = None,
        description: Optional[dict] = None,
    ) -> str:
        """
        Genera un bloque de paso numerado (para guía de usuario) con la imagen.

        Args:
            step_number: Número del paso
            description_text: Texto de instrucción del paso
            capture: Captura de pantalla del paso (opcional)
            description: Metadata de descripción (opcional)
        """
        env_paso = f"paso{self.env_prefix}"
        lines = [f"\\begin{{{env_paso}}}{{{step_number}}}"]
        lines.append(f"  {description_text}")
        lines.append(f"\\end{{{env_paso}}}\n")

        if capture and description:
            lines.append(self.figure_block(capture, description))

        return "\n".join(lines)

    def note_block(self, note_text: str, level: str = "nota") -> str:
        """
        Genera una caja de nota o aviso.

        Args:
            note_text: Texto de la nota
            level: "nota" o "aviso" o "importante"
        """
        if level == "nota":
            env = f"nota{self.env_prefix}"
        else:
            env = f"aviso{self.env_prefix}[{level.capitalize()}]"

        return f"\\begin{{{env}}}\n  {self._escape(note_text)}\n\\end{{{env}}}\n"

    def full_section_file(
        self,
        module: dict,
        captures: list[dict],
        descriptions: list[dict],
    ) -> str:
        """
        Genera el contenido completo de un archivo sections/XX_modulo.tex.

        Args:
            module: dict del módulo de config.MODULES
            captures: Lista de resultados de skill_02_capture
            descriptions: Lista de resultados de skill_04_describe (mismo orden)
        """
        parts = [self.section_header(module)]

        for i, (cap, desc) in enumerate(zip(captures, descriptions)):
            if i == 0:
                # Primera captura: subsección principal con la pantalla completa
                parts.append(self.subsection_block(desc, include_figure=True, capture=cap))
            else:
                # Subsecciones adicionales
                parts.append(self.subsection_block(desc, include_figure=True, capture=cap))

        return "\n".join(parts)

    def write_section_file(
        self,
        module: dict,
        captures: list[dict],
        descriptions: list[dict],
    ) -> str:
        """
        Escribe el archivo .tex en docs/sections/ y retorna la ruta.
        """
        content = self.full_section_file(module, captures, descriptions)
        section_file = module.get("section_file", "XX_modulo")
        out_path = config.SECTIONS_PATH / f"{section_file}.tex"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

        log.info(f"✅  Sección escrita: {out_path}")
        return str(out_path)


# ============================================================
# Ejecución independiente — para ver la salida de un JSON de describe
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill 05 — Escritor LaTeX")
    parser.add_argument("--description", required=True,
        help="Archivo JSON con resultado de skill_04_describe")
    parser.add_argument("--capture",
        help="Archivo JSON con resultado de skill_02_capture (opcional)")
    args = parser.parse_args()

    with open(args.description, encoding="utf-8") as f:
        desc = json.load(f)

    cap = {}
    if args.capture:
        with open(args.capture, encoding="utf-8") as f:
            cap = json.load(f)

    writer = LatexWriter()
    print("\n" + "=" * 60)
    print("  SKILL 05: Bloque LaTeX generado")
    print("=" * 60 + "\n")

    if cap:
        print(writer.subsection_block(desc, include_figure=True, capture=cap))
    else:
        print(writer.subsection_block(desc, include_figure=False))
