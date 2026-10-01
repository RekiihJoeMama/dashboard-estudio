import csv
import os
from datetime import date

import pandas as pd
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(BASE_DIR, "datos", "sesiones.csv")
COLUMNAS = ["fecha", "materia", "minutos", "concentracion", "tema"]
MATERIAS = ["Matematicas", "Fisica", "Programacion", "Ingles", "General"]


def asegurar_csv():
    """Crea el CSV con su cabecera si todavía no existe."""
    if not os.path.exists(RUTA_CSV):
        os.makedirs(os.path.dirname(RUTA_CSV), exist_ok=True)
        with open(RUTA_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(COLUMNAS)


@app.route("/")
def index():
    asegurar_csv()
    df = pd.read_csv(RUTA_CSV).fillna("")
    ultimas = df.tail(10).iloc[::-1].to_dict("records")
    return render_template("index.html", sesiones=ultimas)


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
