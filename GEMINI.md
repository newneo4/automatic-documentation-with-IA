# GEMINI.MD — Instrucciones para Agentes de IA

> **Propósito:** Este archivo define las reglas y convenciones que todo agente de IA (Gemini, Claude, etc.) DEBE seguir al generar, editar o mantener documentación LaTeX en este proyecto. Leer este archivo completo antes de realizar cualquier tarea.

---

## 1. Estructura del Proyecto de Documentación

```
docs/
├── documentacion_tecnica.tex   # Documento principal técnico
├── guia_usuario.tex            # Guía de usuario
├── Makefile                    # Compilación automatizada
├── preambulo/                  # Configuración base LaTeX y colores
├── images/                     # TODAS las imágenes (nunca fuera de aquí)
│   ├── general/
│   └── [nombre-seccion]/
└── sections/                   # Archivos .tex modulares por sección
```

**Regla crítica:** NUNCA colocar imágenes directamente en `docs/`. Siempre deben ir en la subcarpeta correcta dentro de `docs/images/`.

---

## 2. Compilación

- **Comando:** Desde la carpeta `docs/`, ejecutar `make`.
- No modificar directamente el preámbulo en el documento principal, usar los archivos en `docs/preambulo/`.

---

## 3. Inserción de Capturas de Pantalla

- Nomenclatura: `kebab-case-descriptivo.png`
- Usar siempre `\begin{figure}[H]` (posición fija estricta).
- El `\caption{}` debe describir explícitamente lo que se ve en la interfaz (nombrar botones y campos en negritas).

```latex
\begin{figure}[H]
  \centering
  \includegraphics[width=0.85\textwidth, frame]{images/[subcarpeta]/[nombre-imagen].png}
  \caption{Descripción detallada con los campos \\textbf{Usuario} y \\textbf{Contraseña}.}
  \label{fig:[identificador]}
\end{figure}
```

---

## 4. Secciones Modulares

No escribas bloques inmensos en el documento principal. Crea archivos en `docs/sections/` y enlázalos usando `\input{sections/nombre_archivo}`.

---

## 5. Elementos de Diseño Especiales (Cajas de Notas)

El sistema de documentación tiene cajas predefinidas generadas desde la configuración. Consulta el archivo `docs/preambulo/custom_envs.tex` para saber el nombre exacto de tu entorno. (Generalmente es `\begin{nota<project>}` y `\begin{aviso<project>}`).

Ejemplo estándar:
```latex
\begin{nota...}
  Texto de la nota importante.
\end{nota...}
```

---

## 6. Automatización (Agent Skills)

En lugar de tomar capturas manualmente, DEBES utilizar los scripts en `agent_skills/` si estás configurado para ello.

1. Navega a `agent_skills/` y activa el entorno virtual.
2. Ejecuta `python orchestrator.py --module [nombre]` para generar capturas y descripciones de forma autónoma.
