"""Estado del negocio: historial y numeración consecutiva.

El estado vive FUERA de la skill (carpeta salidas/ del proyecto, o la que se
pase por --salidas): el contenedor de claude.ai se reinicia entre sesiones y
la carpeta de la skill es efímera. El consecutivo se DERIVA del historial
(máximo + 1): no hay contador aparte que se pueda desincronizar.
"""

import csv
import re
from pathlib import Path

COLUMNAS = ["numero", "fecha", "cliente_nit", "cliente_nombre",
            "subtotal", "descuento", "iva", "total", "estado"]


def siguiente_numero(ruta_historial: Path, anio: int) -> str:
    """COT-{anio}-NNN leyendo el máximo del historial. Si no existe: 001.

    Solo cuentan los números del año pedido: el consecutivo reinicia cada año.
    Filas con numeración ajena al patrón se ignoran en vez de romper.
    """
    patron = re.compile(rf"^COT-{anio}-(\d+)$")
    maximo = 0
    if ruta_historial.exists():
        with open(ruta_historial, newline="", encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                coincide = patron.match(fila.get("numero", "").strip())
                if coincide:
                    maximo = max(maximo, int(coincide.group(1)))
    return f"COT-{anio}-{maximo + 1:03d}"


def registrar(ruta_historial: Path, fila: dict) -> None:
    """Agrega la fila creando el archivo con encabezados si hace falta."""
    ruta_historial.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not ruta_historial.exists()
    with open(ruta_historial, "a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS, extrasaction="ignore")
        if nuevo:
            escritor.writeheader()
        escritor.writerow({c: fila.get(c, "") for c in COLUMNAS})
