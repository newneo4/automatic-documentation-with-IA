"""
skill_03_annotate.py — Anotaciones visuales sobre capturas de pantalla
=======================================================================
Dibuja recuadros y flechas rojas (#FF0000) sobre las imágenes capturadas
para señalar elementos de la interfaz, siguiendo el estilo del template.

Uso independiente:
    python skill_03_annotate.py --image images/dashboard/dashboard.png \
        --boxes "100,200,400,350" "500,100,700,200"

Cuando se importa:
    annotator = ImageAnnotator()
    result = annotator.add_boxes(image_path, boxes=[(x1,y1,x2,y2), ...])
    result = annotator.add_arrow(image_path, start=(x,y), end=(x,y))
    result = annotator.add_number_labels(image_path, points=[(x,y), ...])
"""

import logging
import sys
import argparse
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import config

log = logging.getLogger("skill_03_annotate")


class ImageAnnotator:
    """Añade anotaciones visuales a capturas de pantalla."""

    def __init__(
        self,
        color: tuple = config.COLOR_ANNOTATION,
        line_width: int = config.ANNOTATION_LINE_WIDTH,
    ):
        self.color = color          # RGB tuple, por defecto rojo puro
        self.line_width = line_width

    def _load(self, image_path: str) -> tuple[Image.Image, Path]:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Imagen no encontrada: {image_path}")
        return Image.open(path).convert("RGB"), path

    def _save_annotated(self, image: Image.Image, path: Path, suffix: str = "-anotado") -> str:
        """Guarda la imagen anotada con sufijo en el mismo directorio."""
        out_path = path.parent / f"{path.stem}{suffix}{path.suffix}"
        image.save(str(out_path))
        log.info(f"  ✅ Imagen anotada guardada: {out_path}")
        return str(out_path)

    def add_boxes(
        self,
        image_path: str,
        boxes: list[tuple[int, int, int, int]],
        labels: Optional[list[str]] = None,
        save_suffix: str = "-anotado",
    ) -> dict:
        """
        Dibuja recuadros rojos sobre la imagen.

        Args:
            image_path: Ruta a la imagen original
            boxes: Lista de (x1, y1, x2, y2) en píxeles
            labels: Lista opcional de etiquetas para cada recuadro
            save_suffix: Sufijo del archivo de salida

        Returns:
            dict con path de la imagen anotada y metadata
        """
        image, path = self._load(image_path)
        draw = ImageDraw.Draw(image)

        for i, (x1, y1, x2, y2) in enumerate(boxes):
            # Recuadro rojo
            draw.rectangle([x1, y1, x2, y2], outline=self.color, width=self.line_width)

            # Etiqueta opcional
            if labels and i < len(labels):
                label = labels[i]
                # Fondo del label
                text_bbox = draw.textbbox((x1, y1 - 20), label)
                draw.rectangle(text_bbox, fill=self.color)
                draw.text((x1, y1 - 20), label, fill=(255, 255, 255))

        out_path = self._save_annotated(image, path, save_suffix)
        return {
            "annotated_path": out_path,
            "original_path": image_path,
            "annotations": [{"type": "box", "coords": b} for b in boxes],
        }

    def add_arrow(
        self,
        image_path: str,
        start: tuple[int, int],
        end: tuple[int, int],
        save_suffix: str = "-anotado",
    ) -> dict:
        """
        Dibuja una flecha roja desde start hasta end.

        Args:
            image_path: Ruta a la imagen original
            start: (x, y) punto de inicio de la flecha
            end: (x, y) punta de la flecha (elemento a señalar)
        """
        import math

        image, path = self._load(image_path)
        draw = ImageDraw.Draw(image)

        # Línea principal
        draw.line([start, end], fill=self.color, width=self.line_width)

        # Cabeza de flecha (triángulo)
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        arrow_size = 15
        angles = [angle + 2.5, angle - 2.5]
        for a in angles:
            x = end[0] - arrow_size * math.cos(a)
            y = end[1] - arrow_size * math.sin(a)
            draw.line([end, (int(x), int(y))], fill=self.color, width=self.line_width)

        out_path = self._save_annotated(image, path, save_suffix)
        return {
            "annotated_path": out_path,
            "original_path": image_path,
            "annotations": [{"type": "arrow", "start": start, "end": end}],
        }

    def add_highlight(
        self,
        image_path: str,
        boxes: list[tuple[int, int, int, int]],
        alpha: int = 60,
        save_suffix: str = "-anotado",
    ) -> dict:
        """
        Añade un resaltado semitransparente rojo sobre áreas de la imagen.

        Args:
            image_path: Ruta a la imagen
            boxes: Lista de (x1, y1, x2, y2)
            alpha: Opacidad del resaltado (0-255)
        """
        image, path = self._load(image_path)
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        for (x1, y1, x2, y2) in boxes:
            draw.rectangle([x1, y1, x2, y2],
                fill=(*self.color, alpha),
                outline=self.color,
                width=self.line_width)

        combined = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
        out_path = self._save_annotated(combined, path, save_suffix)
        return {
            "annotated_path": out_path,
            "original_path": image_path,
            "annotations": [{"type": "highlight", "coords": b} for b in boxes],
        }

    def add_number_labels(
        self,
        image_path: str,
        points: list[tuple[int, int]],
        save_suffix: str = "-numerado",
    ) -> dict:
        """
        Dibuja círculos con números sobre puntos específicos de la imagen.
        Útil para referenciar pasos numerados en la documentación.

        Args:
            points: Lista de (x, y) donde colocar los círculos numerados
        """
        image, path = self._load(image_path)
        draw = ImageDraw.Draw(image)
        radius = 14

        for i, (x, y) in enumerate(points, start=1):
            # Círculo rojo
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=self.color,
                outline=(255, 255, 255),
                width=2,
            )
            # Número blanco centrado
            label = str(i)
            text_bbox = draw.textbbox((0, 0), label)
            text_w = text_bbox[2] - text_bbox[0]
            text_h = text_bbox[3] - text_bbox[1]
            draw.text(
                (x - text_w // 2, y - text_h // 2),
                label,
                fill=(255, 255, 255),
            )

        out_path = self._save_annotated(image, path, save_suffix)
        return {
            "annotated_path": out_path,
            "original_path": image_path,
            "annotations": [{"type": "number", "point": p, "label": i+1}
                           for i, p in enumerate(points)],
        }


# ============================================================
# Ejecución independiente
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill 03 — Anotaciones sobre capturas DRII")
    parser.add_argument("--image", required=True, help="Ruta a la imagen a anotar")
    parser.add_argument("--boxes", nargs="*",
        help='Recuadros como "x1,y1,x2,y2" (ej: "100,200,400,350")')
    parser.add_argument("--numbers", nargs="*",
        help='Puntos numerados como "x,y" (ej: "150,300")')
    args = parser.parse_args()

    annotator = ImageAnnotator()

    if args.boxes:
        boxes = [tuple(map(int, b.split(","))) for b in args.boxes]
        result = annotator.add_boxes(args.image, boxes)
        print(f"✅ Imagen anotada: {result['annotated_path']}")

    if args.numbers:
        points = [tuple(map(int, p.split(","))) for p in args.numbers]
        result = annotator.add_number_labels(args.image, points)
        print(f"✅ Imagen numerada: {result['annotated_path']}")
