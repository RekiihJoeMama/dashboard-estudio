import csv
import os
from datetime import date, timedelta

import pandas as pd
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(BASE_DIR, "datos", "sesiones.csv")
COLUMNAS = ["fecha", "materia", "minutos", "concentracion", "tema"]
MATERIAS = ["Matematicas", "Fisica", "Programacion", "Ingles", "General"]
COLORES = {
    "Matematicas": "#f4a6c0",
    "Fisica": "#e8c872",
    "Programacion": "#b49bdb",
    "Ingles": "#7fd1c7",
    "General": "#a893a8",
}
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def asegurar_csv():
    """Crea el CSV con su cabecera si todavía no existe."""
    if not os.path.exists(RUTA_CSV):
        os.makedirs(os.path.dirname(RUTA_CSV), exist_ok=True)
        with open(RUTA_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(COLUMNAS)


def formatear(minutos):
    """90 -> '1h 30m', 120 -> '2h', 25 -> '25m'."""
    h, m = divmod(int(minutos), 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


def calcular_resumen(df):
    """Arma las tarjetas y los datos de los gráficos. Devuelve None si no hay datos."""
    if df.empty:
        return None

    d = df.copy()
    d["fecha"] = pd.to_datetime(d["fecha"]).dt.date
    d["minutos"] = pd.to_numeric(d["minutos"], errors="coerce").fillna(0)
    d["concentracion"] = pd.to_numeric(d["concentracion"], errors="coerce")

    hoy = date.today()
    por_dia = d.groupby("fecha")["minutos"].sum()
    dias_activos = set(por_dia.index)

    # Racha: días seguidos hasta hoy (o hasta ayer si hoy todavía no estudiaste)
    dia = hoy if hoy in dias_activos else hoy - timedelta(days=1)
    racha = 0
    while dia in dias_activos:
        racha += 1
        dia -= timedelta(days=1)

    # Mejor día de la semana
    d["sem"] = d["fecha"].map(lambda x: x.weekday())
    por_sem = d.groupby("sem")["minutos"].sum()
    mejor_dia = DIAS[int(por_sem.idxmax())]
    mejor_dia_min = por_sem.max()

    # Gráfico 1: horas por día, últimos 14 días (con ceros incluidos)
    ultimos = [hoy - timedelta(days=i) for i in range(13, -1, -1)]
    dias_labels = [x.strftime("%d/%m") for x in ultimos]
    dias_horas = [round(float(por_dia.get(x, 0)) / 60, 2) for x in ultimos]

    # Gráfico 2: horas por materia
    por_materia = d.groupby("materia")["minutos"].sum().sort_values(ascending=False)
    mat_labels = list(por_materia.index)
    mat_horas = [round(float(v) / 60, 2) for v in por_materia.values]
    mat_colores = [COLORES.get(m, "#a893a8") for m in mat_labels]

    # Gráfico 3: concentración promedio (solo filas que tienen concentración)
    conc = d.dropna(subset=["concentracion"]).groupby("materia")["concentracion"].mean()
    conc_labels = list(conc.index)
    conc_vals = [round(float(v), 2) for v in conc.values]
    conc_colores = [COLORES.get(m, "#a893a8") for m in conc_labels]

    return {
        "total_txt": formatear(d["minutos"].sum()),
        "dias_activos": len(dias_activos),
        "racha": racha,
        "mejor_dia": mejor_dia,
        "mejor_dia_txt": formatear(mejor_dia_min),
        "graficos": {
            "dias_labels": dias_labels,
            "dias_horas": dias_horas,
            "mat_labels": mat_labels,
            "mat_horas": mat_horas,
            "mat_colores": mat_colores,
            "conc_labels": conc_labels,
            "conc_vals": conc_vals,
            "conc_colores": conc_colores,
        },
    }


@app.route("/")
def index():
    asegurar_csv()
    df = pd.read_csv(RUTA_CSV, dtype=str).fillna("")
    ultimas = df.tail(10).iloc[::-1].to_dict("records")
    return render_template("index.html", sesiones=ultimas, resumen=calcular_resumen(df))


@app.route("/cargar", methods=["GET", "POST"])
def cargar():
    error = None
    if request.method == "POST":
        materia = request.form.get("materia", "")
        tema = request.form.get("tema", "").strip()
        try:
            minutos = int(request.form.get("minutos", ""))
            concentracion = int(request.form.get("concentracion", ""))
        except ValueError:
            minutos = concentracion = 0

        if materia not in MATERIAS:
            error = "Elegí una materia de la lista."
        elif minutos <= 0:
            error = "Los minutos tienen que ser un número mayor a 0."
        elif not 1 <= concentracion <= 5:
            error = "La concentración va de 1 a 5."
        else:
            asegurar_csv()
            with open(RUTA_CSV, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(
                    [date.today().isoformat(), materia, minutos, concentracion, tema]
                )
            return redirect(url_for("index"))

    return render_template("cargar.html", materias=MATERIAS, error=error)


if __name__ == "__main__":
    app.run(debug=True)