# SteelAtlas — Explorador Metalúrgico, Selector y Laboratorio Virtual de Aceros SAE

Aplicación web interactiva para el análisis de composición química, tratamientos térmicos/mecánicos, validación estadística y simulación de ensayos mecánicos en aceros SAE al carbono y de baja aleación.

🔗 **Ver aplicación interactiva en vivo:** [https://erickbasurto.github.io/steel-atlas-sae/](https://erickbasurto.github.io/steel-atlas-sae/)

---

## Desarrolladores
* **Basurto Valdivieso Erick**
* **Coronel Reveles Guadalupe**

---

## Módulos de la Plataforma (7 Pestañas Interactivas)

1. **Auditoría y Preparación de Datos:** Diagnóstico de los `190` registros originales, corrección documentada de anomalías físicas/OCR, clasificación en 4 familias SAE (`10xx`, `11xx/12xx`, `15xx` y baja aleación) y explorador con búsqueda en tiempo real.
2. **Efecto del % de Carbono:** Regresiones lineales ($r$, $R^2$ y valor $p$) entre el contenido de carbono y `UTS`, `YS`, `Dureza HB` y `Elongación`, con filtro para aislar aceros al carbono simple `10xx` ($n = 87$, $R^2 = 0.8718$ en $UTS$) frente a aceros aleados.
3. **Procesamiento, Recocido y Normalizado:** Comparativa mediante diagramas de caja, esquemas microestructurales SVG y contraste pareado en los 20 grados SAE comunes entre recocido y normalizado.
4. **Análisis Estadístico (ANOVA):** Verificación de supuestos de normalidad (Shapiro–Wilk) y homocedasticidad (Levene), acompañada de contraste paramétrico (**ANOVA**) y no paramétrico (**Kruskal–Wallis**).
5. **Selector SAE e Índice de Tenacidad:** Filtro interactivo de selección de materiales por requisitos de diseño ($YS$ mínimo, elongación mínima y condición) y mapa de compromiso resistencia–ductilidad ($I_T = \text{UTS} \times \text{Elongación}/100$).
6. **Ensayo Virtual de Dureza Brinell (HB):** Simulación física de indentación con esfera de carburo de tungsteno ($D = 10\text{ mm}$, $P = 3000\text{ kgf}$), cálculo real del diámetro de huella $d$ en microscopio óptico y síntesis de audio calibrada por dureza.
7. **Péndulo de Impacto Charpy:** Simulación dinámica de impacto que evalúa fractura frágil frente a deformación dúctil a partir del índice de tenacidad y elongación real de cada grado SAE, con respuesta visual y sonora diferenciada.

---

## Flujo de Trabajo y Reproducibilidad

El proyecto separa el procesamiento estadístico en Python del despliegue visual para garantizar precisión matemática y evitar recargas de cómputo:

1. **Procesamiento Estadístico (`analizar_aceros.py`):** Limpia el dataset original (`Steel- Property and Composition (Carbon Steel).csv`), ejecuta las regresiones y pruebas de hipótesis con `pandas`, `numpy` y `scipy`, y exporta los resultados auditados a `datos_procesados.json`.
2. **Ensamblaje Web (`armar_web.py` $\rightarrow$ `index.html`):** Inyecta `datos_procesados.json` dentro de la plantilla web (`HTML5`, `Tailwind CSS`, `Plotly.js`, `Canvas` y `Web Audio API`) generando un único archivo `index.html` autocontenido.

---

## Estructura del Repositorio
* `index.html` — Aplicación web interactiva desplegada en GitHub Pages.
* `analizar_aceros.py` — Script en Python con la auditoría, limpieza y análisis estadístico.
* `datos_procesados.json` — Dataset limpio y métricas estadísticas exportadas.
* `armar_web.py` — Script de ensamblaje automático entre datos y plantilla web.
* `Steel- Property and Composition (Carbon Steel).csv` — Base de datos original.
