# .latexmkrc — Configuración de latexmk para el Proyecto DRII
# Situar este archivo en la carpeta docs/ o en el home del usuario

# Motor de compilación: pdflatex
$pdf_mode = 1;
$pdflatex = "pdflatex -interaction=nonstopmode -synctex=1 %O %S";

# No generar DVI ni PostScript
$dvi_mode = 0;
$postscript_mode = 0;

# Extensiones de archivos auxiliares a limpiar con latexmk -c
@generated_exts = qw(
  aux  bbl  bcf  blg  fdb_latexmk  fls  idx  ilg  ind
  lof  log  lot  nav  out  run.xml  snm  synctex.gz
  toc  vrb  xdv
);

# Visor de PDF (en Linux: evince, okular, zathura)
# Descomentar según el visor preferido:
# $pdf_previewer = "evince %O %S";
# $pdf_previewer = "okular %O %S";
$pdf_previewer = "zathura %O %S";

# Recompilar si hay cambios en archivos de imágenes
$hash_calc_ignore_pattern{'png'} = '.*';
$hash_calc_ignore_pattern{'jpg'} = '.*';
$hash_calc_ignore_pattern{'jpeg'} = '.*';
$hash_calc_ignore_pattern{'pdf'} = '.*';
