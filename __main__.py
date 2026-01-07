import tkinter as tk
from typing import List

import city_simulator as city
from aco_steiner import MinecraftACOSteiner, Punto
from algoritmo_genetico import generar_ciudad
import algoritmo_genetico as ag
from gdpc import Block
from gdpc.geometry import placeRectOutline

from indirect_parametric_encoding import generar_paleta_edificio, crear_genoma_aleatorio, setup as setup_ipe
from urbanismo import models
from interactive_gen_alg import ejecutar_iga_estetico

root: tk.Tk
# Variable global para el checkbox IGA
usar_iga: tk.BooleanVar


def construir_ciudad(numero_parcelas: int, usar_iga_estetico: bool):
    """
    Construye una ciudad completa: optimización funcional + estética + caminos.

    Args:
        numero_parcelas: Número de parcelas a generar
        usar_iga_estetico: Si True, usa IGA para estética. Si False, genoma aleatorio.
    """
    # ========================================
    # FASE 1: Optimización funcional (GA)
    # ========================================
    print("\n" + "=" * 60)
    print("🏙️ FASE 1: OPTIMIZACIÓN FUNCIONAL")
    print("=" * 60)

    ag.numero_de_parcelas = numero_parcelas
    poblacion, _ = generar_ciudad(10, 200)
    ciudad = poblacion[0]  # Mejor ciudad funcionalmente

    print(f"✓ Ciudad funcional optimizada: {len(ciudad)} parcelas")

    # Nivelar terreno de todas las parcelas
    print("\n🏗️ Nivelando terreno...")
    for i, parcela in enumerate(ciudad):
        print(f"  Parcela {i + 1}/{len(ciudad)}: fitness = {1 / (1 + abs(parcela.funcion_adecuacion())):.3f}")
        parcela.level_plot()

    # ========================================
    # FASE 2: Optimización estética
    # ========================================
    print("\n" + "=" * 60)
    print("🎨 FASE 2: OPTIMIZACIÓN ESTÉTICA")
    print("=" * 60)

    if usar_iga_estetico:
        print("Modo: IGA Interactivo (el usuario elige)")
        genoma_estetico = ejecutar_iga_estetico(root, ciudad)
    else:
        print("Modo: Genoma aleatorio")
        genoma_estetico = crear_genoma_aleatorio()

    # ========================================
    # FASE 3: Construcción con paletas
    # ========================================
    print("\n" + "=" * 60)
    print("🏗️ FASE 3: CONSTRUCCIÓN DE EDIFICIOS")
    print("=" * 60)

    lista_puertas: List[Punto] = []

    for i, parcela in enumerate(ciudad):
        print(f"  Construyendo edificio {i + 1}/{len(ciudad)}...")

        # Aplicar genoma estético para generar paleta
        pos = (parcela.x, parcela.y)
        parcela.paleta = generar_paleta_edificio(
            pos=pos,
            genoma=genoma_estetico
        )

        # Construir
        parcela.construir()

        # Guardar puerta para caminos
        gate = parcela.gate_coord()
        if gate:
            lista_puertas.append(Punto(gate[0], gate[1], parcela.uso))

        city.editor.flushBuffer()

    # ========================================
    # FASE 4: Generación de caminos (ACO)
    # ========================================
    print("\n" + "=" * 60)
    print("🛤️ FASE 4: GENERACIÓN DE CAMINOS")
    print("=" * 60)

    models.load_models()
    aco = MinecraftACOSteiner(terminales=lista_puertas)
    aco.ejecutar_y_construir(verbose=True)

    print("\n" + "=" * 60)
    print("✅ CIUDAD COMPLETADA")
    print("=" * 60)


def main():
    global root, usar_iga

    print("Ejecutando programa...")

    city.setup()
    city.calculate_maps()
    setup_ipe()  # Inicializar indirect parametric encoding

    # ==============================
    # Ventana principal
    # ==============================
    root = tk.Tk()
    root.title("Generador de Ciudades Minecraft")
    root.geometry("900x700")
    root.configure(bg="#2c3e50")
    usar_iga = tk.BooleanVar(value=False)
    # ==============================
    # Panel de controles (izquierda)
    # ==============================
    frame_controles = tk.Frame(root, bg="#34495e", relief="ridge", borderwidth=2)
    frame_controles.pack(side="left", fill="y", padx=10, pady=10)

    # Título del panel
    tk.Label(
        frame_controles,
        text="Panel de Control",
        font=("Arial", 16, "bold"),
        bg="#34495e",
        fg="white",
        pady=15
    ).pack()

    # Separador
    tk.Frame(frame_controles, height=2, bg="#7f8c8d").pack(fill="x", padx=20, pady=5)

    # ========== Delinear zona ==========
    tk.Label(
        frame_controles,
        text="Zona de Construcción",
        font=("Arial", 11, "bold"),
        bg="#34495e",
        fg="#ecf0f1",
        pady=5
    ).pack()

    tk.Button(
        frame_controles,
        text="📍 Delinear Zona",
        command=lambda: (
            placeRectOutline(city.editor, city.buildArea.toRect(), 140, Block("spruce_leaves")),
            city.editor.flushBuffer()
        ),
        bg="#3498db",
        fg="white",
        font=("Arial", 10, "bold"),
        padx=20,
        pady=8,
        relief="raised",
        borderwidth=2
    ).pack(pady=5, padx=20)

    # ========== Refrescar mapas ==========
    tk.Label(
        frame_controles,
        text="Actualizar Información",
        font=("Arial", 11, "bold"),
        bg="#34495e",
        fg="#ecf0f1",
        pady=5
    ).pack(pady=(15, 5))

    tk.Button(
        frame_controles,
        text="🔄 Refrescar Mapas",
        command=lambda: city.refresh_maps(),
        bg="#9b59b6",
        fg="white",
        font=("Arial", 10, "bold"),
        padx=20,
        pady=8,
        relief="raised",
        borderwidth=2
    ).pack(pady=5, padx=20)

    # Separador
    tk.Frame(frame_controles, height=2, bg="#7f8c8d").pack(fill="x", padx=20, pady=15)

    # ========== Configuración de ciudad ==========
    tk.Label(
        frame_controles,
        text="Configuración de Ciudad",
        font=("Arial", 11, "bold"),
        bg="#34495e",
        fg="#ecf0f1",
        pady=5
    ).pack()

    # Número de parcelas
    tk.Label(
        frame_controles,
        text="Número de parcelas:",
        font=("Arial", 10),
        bg="#34495e",
        fg="#bdc3c7"
    ).pack(pady=(10, 2))

    entrada_parcelas = tk.Entry(
        frame_controles,
        width=20,
        font=("Arial", 11),
        justify="center",
        relief="solid",
        borderwidth=1
    )
    entrada_parcelas.pack(pady=5, padx=20)
    entrada_parcelas.insert(0, "10")  # Valor por defecto

    # Checkbox para IGA
    check_iga = tk.Checkbutton(
        frame_controles,
        text="Usar IGA para estética",
        variable=usar_iga,
        font=("Arial", 10),
        bg="#34495e",
        fg="#ecf0f1",
        selectcolor="#2c3e50",
        activebackground="#34495e",
        activeforeground="white"
    )
    check_iga.pack(pady=10)

    # Tooltip/descripción
    tk.Label(
        frame_controles,
        text="(Si está marcado, podrás elegir\nel estilo interactivamente)",
        font=("Arial", 8),
        bg="#34495e",
        fg="#95a5a6",
        justify="left"
    ).pack(pady=2)

    # Botón construir ciudad
    tk.Button(
        frame_controles,
        text="🏗️ Construir Ciudad",
        command=lambda: construir_ciudad(
            int(entrada_parcelas.get()),
            usar_iga.get()
        ),
        bg="#27ae60",
        fg="white",
        font=("Arial", 12, "bold"),
        padx=30,
        pady=12,
        relief="raised",
        borderwidth=3
    ).pack(pady=20, padx=20)

    # ==============================
    # Panel de mapas (derecha)
    # ==============================
    frame_derecha = tk.Frame(root, bg="#2c3e50")
    frame_derecha.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    # Título del panel de mapas
    tk.Label(
        frame_derecha,
        text="Visualización del Terreno",
        font=("Arial", 16, "bold"),
        bg="#2c3e50",
        fg="white",
        pady=10
    ).pack()

    # Canvas para el mapa
    frame_canvas = tk.Frame(frame_derecha, bg="#34495e", relief="sunken", borderwidth=3)
    frame_canvas.pack(pady=10, padx=10)

    city.canvas = tk.Canvas(
        frame_canvas,
        width=city.width * city.cell_size,
        height=city.height * city.cell_size,
        bg="#1a1a1a",
        highlightthickness=0
    )
    city.canvas.pack(padx=5, pady=5)

    # Botones de mapas
    frame_botones_mapa = tk.Frame(frame_derecha, bg="#2c3e50")
    frame_botones_mapa.pack(pady=10)

    botones_mapa = [
        ("🟢 Bloques", "blocks", "#27ae60"),
        ("⛰️ Altitud", "height", "#3498db"),
        ("📐 Inclinación", "inclination", "#e67e22"),
        ("🏗️ Edificabilidad", "buildable", "#9b59b6")
    ]

    for texto, tipo, color in botones_mapa:
        tk.Button(
            frame_botones_mapa,
            text=texto,
            command=lambda t=tipo: city.draw_map(t),
            bg=color,
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            relief="raised",
            borderwidth=2
        ).pack(side="left", padx=5)

    # Dibujar mapa inicial
    city.draw_map("blocks")

    # Iniciar loop
    root.mainloop()


if __name__ == "__main__":
    main()