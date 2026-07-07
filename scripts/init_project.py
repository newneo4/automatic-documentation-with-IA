import configparser
import os
import re

def main():
    print("Iniciando configuración del proyecto de documentación...")
    
    # 1. Leer configuración
    config = configparser.ConfigParser()
    if not os.path.exists('project.conf'):
        print("Error: No se encontró 'project.conf'. Ejecute este script desde la raíz del template.")
        return
    config.read('project.conf', encoding='utf-8')
    
    project_name = config.get('project', 'name', fallback='Project')
    full_name = config.get('project', 'full_name', fallback='Sistema')
    institution = config.get('project', 'institution', fallback='Institucion')
    department = config.get('project', 'department', fallback='')
    language = config.get('project', 'language', fallback='spanish')
    version = config.get('project', 'version', fallback='1.0')
    
    tech_doc = config.get('documents', 'technical_doc', fallback='documentacion_tecnica')
    user_doc = config.get('documents', 'user_guide', fallback='guia_usuario')
    tech_footer = config.get('documents', 'technical_footer', fallback='Documentación Técnica')
    user_footer = config.get('documents', 'user_guide_footer', fallback='Guía de Usuario')
    
    c_primary = config.get('colors', 'primary', fallback='0, 82, 155')
    c_accent = config.get('colors', 'accent', fallback='255, 107, 0')
    c_annotation = config.get('colors', 'annotation', fallback='255, 0, 0')
    
    env_prefix = config.get('agent_skills', 'env_prefix', fallback='nota').lower()
    prefix_camel = env_prefix.capitalize() + project_name.capitalize()
    prefix_lower = (env_prefix + project_name).lower()
    
    # 2. Generar colors.tex
    colors_content = f"""% === PALETA DE COLORES INSTITUCIONAL ===
\\definecolor{{{prefix_lower}Primary}}{{RGB}}{{{c_primary}}}
\\definecolor{{{prefix_lower}Accent}}{{RGB}}{{{c_accent}}}
\\definecolor{{{prefix_lower}Annotation}}{{RGB}}{{{c_annotation}}}
\\definecolor{{{prefix_lower}Black}}{{RGB}}{{30, 30, 30}}
\\definecolor{{{prefix_lower}Gray}}{{RGB}}{{100, 100, 100}}
\\definecolor{{{prefix_lower}LightGray}}{{RGB}}{{245, 245, 245}}
\\definecolor{{{prefix_lower}Border}}{{RGB}}{{0, 0, 0}}
"""
    with open('docs/preambulo/colors.tex', 'w', encoding='utf-8') as f:
        f.write(colors_content)
    
    # 3. Generar custom_envs.tex
    envs_content = f"""% === CAJAS DE NOTAS Y AVISOS ===
\\newenvironment{{{prefix_lower}}}[1][Nota]{{%
  \\begin{{mdframed}}[
    backgroundcolor={prefix_lower}LightGray,
    linecolor={prefix_lower}Primary,
    linewidth=1pt,
    leftmargin=0pt, rightmargin=0pt,
    innerleftmargin=10pt, innerrightmargin=10pt,
    innertopmargin=8pt, innerbottommargin=8pt
  ]
  \\textbf{{\\textcolor{{{prefix_lower}Primary}}#1:}}\\ %
}}{{%
  \\end{{mdframed}}
}}

\\newenvironment{{aviso{project_name.lower()}}}[1][Importante]{{%
  \\begin{{mdframed}}[
    backgroundcolor={prefix_lower}LightGray,
    linecolor={prefix_lower}Accent,
    linewidth=2pt,
    leftmargin=0pt, rightmargin=0pt,
    innerleftmargin=10pt, innerrightmargin=10pt,
    innertopmargin=8pt, innerbottommargin=8pt
  ]
  \\textbf{{\\textcolor{{{prefix_lower}Accent}}#1:}}\\ %
}}{{%
  \\end{{mdframed}}
}}
"""
    with open('docs/preambulo/custom_envs.tex', 'w', encoding='utf-8') as f:
        f.write(envs_content)
        
    # 4. Generar header_footer.tex para técnica y usuario
    def gen_hf(title, footer_text):
        return f"""\\pagestyle{{fancy}}
\\fancyhf{{}}
\\renewcommand{{\\headrulewidth}}{{0.4pt}}
\\renewcommand{{\\footrulewidth}}{{0.4pt}}
\\fancyhead[L]{{}}
\\fancyhead[R]{{\\small\\textbf{{{title.upper()}}}}}
\\fancyfoot[L]{{\\small\\textcolor{{{prefix_lower}Gray}}{{{footer_text}}}}}
\\fancyfoot[R]{{\\small Página \\thepage\\ de \\pageref{{LastPage}}}}
"""
    with open('docs/preambulo/header_footer_tech.tex', 'w', encoding='utf-8') as f:
        f.write(gen_hf(f"Documentación Técnica - {project_name}", tech_footer))
    with open('docs/preambulo/header_footer_user.tex', 'w', encoding='utf-8') as f:
        f.write(gen_hf(f"Guía de Usuario - {project_name}", user_footer))
        
    # 5. Generar documentos principales a partir del template genérico
    with open('docs/templates/documento_principal.tex', 'r', encoding='utf-8') as f:
        doc_template = f.read()
        
    def render_doc(doc_type, filename, hf_file, title):
        content = doc_template.replace('{{LANGUAGE}}', language)
        content = content.replace('{{PREFIX}}', prefix_lower)
        content = content.replace('{{HF_FILE}}', hf_file)
        content = content.replace('{{INSTITUTION}}', institution.upper())
        content = content.replace('{{DEPARTMENT}}', department)
        content = content.replace('{{TITLE}}', title.upper())
        content = content.replace('{{VERSION}}', version)
        content = content.replace('{{FULL_NAME}}', full_name)
        with open(f'docs/{filename}.tex', 'w', encoding='utf-8') as f:
            f.write(content)
            
    render_doc('technical', tech_doc, 'header_footer_tech', f'DOCUMENTACIÓN TÉCNICA\n{full_name}')
    render_doc('user', user_doc, 'header_footer_user', f'GUÍA DE USUARIO\n{full_name}')

    # 6. Crear Makefile
    makefile = f"""LATEX      = pdflatex
LATEXFLAGS = -interaction=nonstopmode -file-line-error
TECNICA_SRC = {tech_doc}.tex
GUIA_SRC    = {user_doc}.tex
TECNICA_PDF = {tech_doc}.pdf
GUIA_PDF    = {user_doc}.pdf

.PHONY: all tecnica guia clean purge

all: tecnica guia

tecnica:
\t@echo "Compilando Documentacion Tecnica..."
\t$(LATEX) $(LATEXFLAGS) $(TECNICA_SRC)
\t$(LATEX) $(LATEXFLAGS) $(TECNICA_SRC)
\t@echo "OK  $(TECNICA_PDF) generado."

guia:
\t@echo "Compilando Guia de Usuario..."
\t$(LATEX) $(LATEXFLAGS) $(GUIA_SRC)
\t$(LATEX) $(LATEXFLAGS) $(GUIA_SRC)
\t@echo "OK  $(GUIA_PDF) generado."

clean:
\t@rm -f *.aux *.log *.toc *.out *.fls *.fdb_latexmk *.synctex.gz *.bbl *.blg *.lof *.lot *.idx *.ind *.ilg *.nav *.snm *.vrb

purge: clean
\t@rm -f $(TECNICA_PDF) $(GUIA_PDF)
"""
    with open('docs/Makefile', 'w', encoding='utf-8') as f:
        f.write(makefile)

    # 7. Config agent skills
    if os.path.exists('agent_skills/config.template.py'):
        with open('agent_skills/config.template.py', 'r', encoding='utf-8') as f:
            content = f.read()
            content = content.replace('{{BASE_URL}}', config.get('agent_skills', 'base_url', fallback='http://localhost:3000'))
            content = content.replace('{{LOGIN_URL}}', config.get('agent_skills', 'login_url', fallback='/login'))
            content = content.replace('{{ENV_PREFIX}}', env_prefix)
            content = content.replace('{{PROJECT_NAME}}', full_name)
        with open('agent_skills/config.py', 'w', encoding='utf-8') as f:
            f.write(content)

    print("¡Inicialización completa! Archivos generados correctamente.")

if __name__ == '__main__':
    main()
