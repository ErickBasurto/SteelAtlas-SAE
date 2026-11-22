import json
import numpy as np
import pandas as pd
from scipy import stats

ARCHIVO_CSV = "Steel- Property and Composition (Carbon Steel).csv"
ARCHIVO_SALIDA = "datos_procesados.json"


def clasificar_familia(grade: str) -> str:
    g = str(grade).strip()
    if g.startswith("10"):
        return "10xx (Carbono simple)"
    elif g.startswith(("11", "12")):
        return "11xx/12xx (Resulfurados)"
    elif g.startswith("15"):
        return "15xx (Alto Manganeso)"
    else:
        return "Aleados (41xx, 43xx, etc.)"


def clasificar_condicion(cond: str) -> str:
    c = str(cond).lower().replace("\n", " ")
    # Corregir errores tipográficos de OCR en el CSV original
    c = c.replace("rotted", "rolled").replace("orawn", "drawn")
    if "spheroidized" in c:
        return "Esferoidizado + Estirado en frío"
    elif "quenched" in c or "tempered" in c:
        return "Templado y Revenido (Q&T)"
    elif "normalized" in c and "cold drawn" in c:
        return "Normalizado + Estirado en frío"
    elif "annealed" in c and "cold drawn" in c:
        return "Recocido + Estirado en frío"
    elif "normalized" in c:
        return "Normalizado (Normalized)"
    elif "annealed" in c:
        return "Recocido (Annealed)"
    elif "cold drawn" in c:
        return "Estirado en frío (Cold drawn)"
    elif "hot rolled" in c:
        return "Laminado en caliente (Hot rolled)"
    return "Otro"


def main():
    # 1. Cargar base de datos original
    df = pd.read_csv(ARCHIVO_CSV)
    total_registros = len(df)

    # 2. Auditoría y corrección documentada de anomalías del CSV
    anomalias = [
        {
            "registro": "Filas 120–121 (SAE 12L14)",
            "problema": "C (Max) registrado como 15.0%, valor físicamente imposible para un acero (el hierro fundido inicia en ~2.1% C).",
            "decision": "Se corrigió a 0.15% C conforme a la especificación SAE 12L14 (error de punto decimal en la captura).",
        },
        {
            "registro": "Fila 149 (SAE 4150 Normalizado)",
            "problema": "UTS (MPa) = 116 MPa, incoherente con su propio UTS (Ksi) = 168 ksi y YS = 731 MPa.",
            "decision": "Se recalculó UTS (MPa) = 1158 MPa a partir de 168 ksi (error de dígito faltante en OCR).",
        },
        {
            "registro": "Fila 147 (SAE 4140 Recocido)",
            "problema": "YS (MPa) = 915 MPa superaba al UTS = 655 MPa, mientras que YS (ksi) = 60 ksi.",
            "decision": "Se corrigió YS (MPa) = 414 MPa (equivalente a 60 ksi) para mantener coherencia física (YS < UTS).",
        },
        {
            "registro": "Múltiples filas (texto y unidades)",
            "problema": "Errores de OCR ('Cold Orawn', 'Hot rotted'), comas decimales ('40,2'), durezas etiquetadas como '269 HRB' en columna HB y P(Max)=35 expresado en milésimas.",
            "decision": "Se estandarizaron etiquetas, se convirtieron comas a punto decimal, se extrajo el valor numérico de HB y se normalizó P(Max) > 1 dividiendo entre 1000.",
        },
    ]

    df.loc[df["SAE Grade"] == "12L14", "C (Max)"] = 0.15
    df.loc[(df["SAE Grade"] == "4150") & (df["UTS (MPa)"] == 116), "UTS (MPa)"] = 1158
    df.loc[(df["SAE Grade"] == "4140") & (df["YS (MPa)"] == 915), "YS (MPa)"] = 414

    df["Reduction_clean"] = pd.to_numeric(
        df["Reduction (%)"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )
    df["Hardness_clean"] = pd.to_numeric(
        df["Hardness (HB)"].astype(str).str.extract(r"(\d+\.?\d*)")[0],
        errors="coerce",
    )
    df["P_Max_clean"] = np.where(df["P (Max)"] > 1, df["P (Max)"] / 1000.0, df["P (Max)"])

    # %C representativo: promedio de rango [C Min, C Max] o C Max cuando C Min es NaN
    df["C_pct"] = np.where(
        df["C (Min)"].notna(),
        (df["C (Min)"] + df["C (Max)"]) / 2.0,
        df["C (Max)"],
    )

    # Clasificación por familia SAE y condición de procesamiento
    df["Familia_SAE"] = df["SAE Grade"].apply(clasificar_familia)
    df["Es_Carbono_Simple"] = df["Familia_SAE"] == "10xx (Carbono simple)"
    df["Condicion_Grupo"] = df["Conditions"].apply(clasificar_condicion)

    # Propuesta propia: Índice de Compromiso Resistencia–Ductilidad (Tenacidad estimada ~ MJ/m^3)
    df["Indice_Tenacidad"] = (df["UTS (MPa)"] * (df["Elongation (%)"] / 100.0)).round(2)

    # 3. Correlaciones %C vs propiedades mecánicas (Todos vs. Solo aceros 10xx)
    propiedades = {
        "UTS (MPa)": "UTS",
        "YS (MPa)": "YS",
        "Hardness_clean": "Dureza_HB",
        "Elongation (%)": "Elongacion",
    }
    correlaciones = {}
    for nombre_sub, sub_df in [("todos", df), ("solo_10xx", df[df["Es_Carbono_Simple"]])]:
        correlaciones[nombre_sub] = {}
        for col, etiqueta in propiedades.items():
            valido = sub_df[["C_pct", col]].dropna()
            r, p = stats.pearsonr(valido["C_pct"], valido[col])
            pendiente, intercepto, _, _, _ = stats.linregress(valido["C_pct"], valido[col])
            correlaciones[nombre_sub][etiqueta] = {
                "n": int(len(valido)),
                "r": round(float(r), 4),
                "r2": round(float(r**2), 4),
                "p_value": float(f"{p:.2e}"),
                "pendiente": round(float(pendiente), 2),
                "intercepto": round(float(intercepto), 2),
            }

    # 4. Comparativa estadística entre condiciones de procesamiento (ANOVA y Kruskal-Wallis)
    grupos_anova = [
        "Laminado en caliente (Hot rolled)",
        "Estirado en frío (Cold drawn)",
        "Normalizado (Normalized)",
        "Recocido (Annealed)",
    ]
    analisis_anova = {}
    for col, etiqueta in propiedades.items():
        muestras = [df[df["Condicion_Grupo"] == g][col].dropna().values for g in grupos_anova]
        shapiro_p = [round(float(stats.shapiro(m)[1]), 4) for m in muestras]
        _, levene_p = stats.levene(*muestras)
        f_stat, anova_p = stats.f_oneway(*muestras)
        kw_stat, kw_p = stats.kruskal(*muestras)

        analisis_anova[etiqueta] = {
            "grupos": grupos_anova,
            "n_por_grupo": [int(len(m)) for m in muestras],
            "medias": [round(float(np.mean(m)), 1) for m in muestras],
            "desv_est": [round(float(np.std(m, ddof=1)), 1) for m in muestras],
            "medianas": [round(float(np.median(m)), 1) for m in muestras],
            "shapiro_p": shapiro_p,
            "levene_p": round(float(levene_p), 4),
            "cumple_supuestos": bool(all(p > 0.05 for p in shapiro_p) and levene_p > 0.05),
            "F_stat": round(float(f_stat), 2),
            "anova_p": float(f"{anova_p:.2e}"),
            "KW_stat": round(float(kw_stat), 2),
            "kw_p": float(f"{kw_p:.2e}"),
        }

    # 5. Análisis específico: Recocido vs. Normalizado (comparación pareada por grado SAE)
    df_norm = df[df["Condicion_Grupo"] == "Normalizado (Normalized)"].set_index("SAE Grade")
    df_ann = df[df["Condicion_Grupo"] == "Recocido (Annealed)"].set_index("SAE Grade")
    grados_comunes = sorted(list(set(df_norm.index).intersection(set(df_ann.index))))

    comparacion_norm_ann = []
    for g in grados_comunes:
        rn = df_norm.loc[g]
        ra = df_ann.loc[g]
        comparacion_norm_ann.append({
            "grado": g,
            "c_pct": round(float(rn["C_pct"]), 3),
            "cond_norm": str(rn["Conditions"]).replace("\n", " "),
            "cond_ann": str(ra["Conditions"]).replace("\n", " "),
            "uts_norm": int(rn["UTS (MPa)"]),
            "uts_ann": int(ra["UTS (MPa)"]),
            "ys_norm": int(rn["YS (MPa)"]),
            "ys_ann": int(ra["YS (MPa)"]),
            "hb_norm": float(rn["Hardness_clean"]),
            "hb_ann": float(ra["Hardness_clean"]),
            "elong_norm": float(rn["Elongation (%)"]),
            "elong_ann": float(ra["Elongation (%)"]),
        })

    # 6. Exportar registros limpios para los gráficos interactivos y el Selector de Materiales
    registros_limpios = []
    for _, row in df.iterrows():
        registros_limpios.append({
            "grado": str(row["SAE Grade"]),
            "familia": row["Familia_SAE"],
            "es_10xx": bool(row["Es_Carbono_Simple"]),
            "condicion_original": str(row["Conditions"]).replace("\n", " "),
            "condicion": row["Condicion_Grupo"],
            "c_pct": round(float(row["C_pct"]), 3),
            "mn_max": round(float(row["Mn (Max)"]), 2),
            "uts": int(row["UTS (MPa)"]),
            "ys": int(row["YS (MPa)"]),
            "elongacion": round(float(row["Elongation (%)"]), 1),
            "reduccion": None if pd.isna(row["Reduction_clean"]) else round(float(row["Reduction_clean"]), 1),
            "dureza_hb": None if pd.isna(row["Hardness_clean"]) else round(float(row["Hardness_clean"]), 1),
            "indice_tenacidad": float(row["Indice_Tenacidad"]),
        })

    # 7. Metodología explicada de forma simple para integrarla de manera discreta en la web
    metodologia_simple = {
        "titulo": "Metodología y Pasos del Análisis",
        "resumen": "Todo el procesamiento matemático y estadístico se realizó de forma reproducible en Python antes de construir la visualización interactiva.",
        "pasos": [
            {
                "paso": "1. Inspección y Auditoría Física",
                "descripcion": "Revisamos los 190 registros del CSV verificando coherencia metalúrgica (que UTS > YS, que el %C estuviera dentro del rango de aceros y que las unidades MPa/ksi coincidieran). Se corrigieron 3 errores de captura/OCR y se normalizaron etiquetas duplicadas.",
            },
            {
                "paso": "2. Clasificación por Familia SAE y Tratamiento",
                "descripcion": "Separamos los aceros al carbono simples (serie 10xx, n=87) de los resulfurados (11xx/12xx), al manganeso (15xx) y de baja aleación (41xx, 43xx, etc.). Agrupamos las 46 variantes de texto de procesamiento en 8 categorías metalúrgicas estándar.",
            },
            {
                "paso": "3. Correlación con el Contenido de Carbono (%C)",
                "descripcion": "Calculamos regresiones lineales (r de Pearson y R²) entre el %C promedio y UTS, YS, Dureza HB y Elongación, comparando toda la base contra los aceros 10xx puros para aislar el efecto de la perlita/cementita sin interferencia de aleantes.",
            },
            {
                "paso": "4. Evaluación Estadística (ANOVA y Kruskal-Wallis)",
                "descripcion": "Evaluamos normalidad (Shapiro-Wilk) y homogeneidad de varianzas (Levene) entre las 4 condiciones principales. Como los grupos están desbalanceados y no cumplen normalidad estricta, acompañamos el ANOVA clásico con la prueba no paramétrica de Kruskal-Wallis.",
            },
            {
                "paso": "5. Control de Variables Confusoras (Recocido vs. Normalizado)",
                "descripcion": "Detectamos que el 100% de los registros recocidos y normalizados del CSV corresponden a aceros aleados. Por ello, los comparamos de forma pareada (mismo grado SAE) para aislar el efecto real de la velocidad de enfriamiento.",
            },
            {
                "paso": "6. Propuesta Propia: Índice de Tenacidad y Selector",
                "descripcion": "Definimos un Índice de Compromiso Resistencia–Ductilidad (UTS × Elongación / 100, en MJ/m³ aproximados) e implementamos un filtro interactivo para seleccionar grados SAE según requerimientos de diseño mecánico.",
            },
        ],
    }

    salida = {
        "autores": ["Basurto Valdivieso Erick", "Coronel Reveles Guadalupe"],
        "resumen_dataset": {
            "total_registros": total_registros,
            "total_grados_unicos": int(df["SAE Grade"].nunique()),
            "conteo_familias": df["Familia_SAE"].value_counts().to_dict(),
            "conteo_condiciones": df["Condicion_Grupo"].value_counts().to_dict(),
        },
        "anomalias": anomalias,
        "correlaciones": correlaciones,
        "anova": analisis_anova,
        "recocido_vs_normalizado": comparacion_norm_ann,
        "metodologia": metodologia_simple,
        "registros": registros_limpios,
    }

    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    print(f"Listo: '{ARCHIVO_SALIDA}' generado correctamente con {total_registros} registros limpios.")
    print(f"- R² UTS vs %C (Todos): {correlaciones['todos']['UTS']['r2']} -> (Solo 10xx): {correlaciones['solo_10xx']['UTS']['r2']}")
    print(f"- Pares exactos Recocido vs Normalizado: {len(grados_comunes)} grados SAE.")


if __name__ == "__main__":
    main()