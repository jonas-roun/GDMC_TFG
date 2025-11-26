import tkinter as tk
from typing import List

import city_simulator as city
from aco_steiner import MinecraftACOSteiner, Punto
from algoritmo_genetico import generar_ciudad
import algoritmo_genetico as ag
from gdpc import  Block
from gdpc.geometry import placeCuboid, placeRectOutline

from urbanismo import models


def construir_ciudad(numero_parcelas: int):
    ag.numero_de_parcelas = numero_parcelas
    poblacion, _ = generar_ciudad(10, 200)
    ciudad = poblacion[0]  # ahora sí es un GenomaCiudad (lista de parcelas)
    lista_puertas:List[Punto] = []
    for i in range(len(ciudad)):
        print("parcela: ", ciudad[i],"->", 1/(1+abs(ciudad[i].funcion_adecuacion())))
        ciudad[i].level_plot()
        ciudad[i].construir()
        lista_puertas.append(Punto(ciudad[i].gate_coord()[0], ciudad[i].gate_coord()[1],ciudad[i].uso))
        city.editor.flushBuffer()
    #

    models.load_models()
    aco = MinecraftACOSteiner(
        terminales=lista_puertas
    )

    # Ejecutar y construir el camino automáticamente
    aco.ejecutar_y_construir(verbose=True)

def main():
    print("Ejecutando programa...")

    city.setup()
    city.calculate_maps()

    # ==============================
    # Tkinter
    # ==============================
    root = tk.Tk()
    root.title("Mapa Minecraft")

    frame_controles = tk.Frame(root)

    tk.Button(frame_controles, text="Delinear zona de construcción",
              command=lambda: (placeRectOutline(city.editor, city.buildArea.toRect(), 140, Block("spruce_leaves")), city.editor.flushBuffer())).pack(
        side="top", expand=True)

    refresh_icon = tk.PhotoImage(file="data/img/refresh.png")
    tk.Button(frame_controles, text="Refrescar mapas", image=refresh_icon,
              command=lambda: city.refresh_maps()).pack(
        side="top", expand=True)


    # Etiqueta
    tk.Label(frame_controles, text="Número de parcelas:").pack(pady=5)

    # Caja de texto (una línea)
    entrada = tk.Entry(frame_controles, width=30)
    entrada.pack(pady=5)

    tk.Button(frame_controles, text="Construir ciudad", command=lambda: construir_ciudad(int(entrada.get()))).pack(side="top", expand=True)

    frame_controles.pack(side="right", fill="y")  # pegado a la izquierda

    frame_mapa = tk.Frame(root)
    frame_mapa.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    city.canvas = tk.Canvas(frame_mapa, width=city.width * city.cell_size, height=city.height * city.cell_size)
    city.canvas.pack()

    tk.Button(frame_mapa, text="Mapa por Bloques", command=lambda: city.draw_map("blocks")).pack(side="left")
    tk.Button(frame_mapa, text="Mapa por Altitud", command=lambda: city.draw_map("height")).pack(side="left")
    tk.Button(frame_mapa, text="Mapa por Inclinación", command=lambda: city.draw_map("inclination")).pack(side="left")
    tk.Button(frame_mapa, text="Mapa por Edificabilidad", command=lambda: city.draw_map("buildable")).pack(side="left")

    frame_mapa.pack(side="left", fill="both", expand=True)  # ocupa el resto

    city.draw_map("blocks")
    root.mainloop()


if __name__ == "__main__":
    main()
