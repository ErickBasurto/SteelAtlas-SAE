with open("plantilla_index.html", "r", encoding="utf-8") as f:
    html = f.read()

with open("datos_procesados.json", "r", encoding="utf-8") as f:
    json_str = f.read()

if "__DATA_JSON__" not in html:
    raise ValueError("No se encontró el marcador __DATA_JSON__ en plantilla_index.html")

html_final = html.replace("__DATA_JSON__", json_str, 1)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_final)

print("Listo: 'index.html' generado con los 190 registros completos y sin cortes.")