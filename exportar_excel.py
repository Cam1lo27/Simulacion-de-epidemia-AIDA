import os
from datetime import datetime
import pandas as pd


def exportar_a_excel(historial, parametros):
    if len(historial) == 0:
        return None

    if not os.path.exists("resultados"):
        os.makedirs("resultados")

    nombre_archivo = "resultados/simulacion_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".xlsx"

    tabla_datos = pd.DataFrame(historial)
    tabla_parametros = pd.DataFrame(list(parametros.items()), columns=["Parametro", "Valor"])

    with pd.ExcelWriter(nombre_archivo) as escritor:
        tabla_datos.to_excel(escritor, sheet_name="Datos", index=False)
        tabla_parametros.to_excel(escritor, sheet_name="Parametros", index=False)

    return nombre_archivo
