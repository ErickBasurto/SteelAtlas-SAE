# SteelAtlas — Explorador Metalúrgico y Selector de Aceros SAE

Aplicación web interactiva para el análisis de composición química, tratamientos térmicos/mecánicos y propiedades mecánicas de aceros SAE al carbono y de baja aleación.

🔗 **Ver aplicación interactiva en vivo:** [https://TU-USUARIO.github.io/steel-atlas-sae/](https://TU-USUARIO.github.io/steel-atlas-sae/)

---

## Desarrolladores
* **Basurto Valdivieso Erick**
* **Coronel Reveles Guadalupe**

---

## Arquitectura y Flujo de Trabajo

El proyecto separa el procesamiento estadístico del despliegue visual para garantizar exactitud matemática y reproducibilidad:

1. **Auditoría y Procesamiento (`analizar_aceros.py`):**
   * Limpieza y validación física de los `190` registros originales del dataset (`Steel- Property and Composition (Carbon Steel).csv`), corrigiendo inconsistencias de captura/OCR (como el `%C` del grado `12L14` y discrepancias MPa/ksi en `4140` y `4150`).
   * Clasificación en 4 familias metalúrgicas (`10xx` carbono simple, `11xx/12xx` resulfurados, `15xx` alto manganeso y aceros aleados `41xx/43xx`) y estandarización de condiciones de procesamiento.
   * Cálculo de regresiones lineales (`r` de Pearson, `R²`), verificación de supuestos (Shapiro-Wilk y Levene), contraste de hipótesis mediante **ANOVA** y **Kruskal-Wallis**, comparación pareada de **Recocido vs. Normalizado** y cálculo del **Índice de Compromiso Resistencia–Ductilidad** ($I_T = \text{UTS} \times \text{Elongación}/100$).
   * Exportación de resultados auditados a `datos_procesados.json`.

2. **Ensamblaje y Visualización (`armar_web.py` $\rightarrow$ `index.html`):**
   * Inyección de `datos_procesados.json` en una aplicación web autocontenida construida con HTML5, Tailwind CSS y Plotly.js, equipada con filtros en tiempo real, diagramas microestructurales y un selector interactivo de grados SAE.

---

## Estructura del Repositorio
* `index.html` — Aplicación web interactiva lista para navegador y despliegue en GitHub Pages.
* `analizar_aceros.py` — Script en Python (`pandas`, `numpy`, `scipy`) con toda la limpieza y análisis estadístico.
* `datos_procesados.json` — Datos limpios y métricas estadísticas exportadas.
* `armar_web.py` — Script de ensamblaje entre datos y plantilla web.
* `Steel- Property and Composition (Carbon Steel).csv` — Base de datos original.
