# ========================================
# REEMPLAZA EL INICIO DE interactive_gen_alg.py
# (desde los imports hasta la función ejecutar_iga_estetico)
# ========================================

import tkinter as tk
from tkinter import messagebox
from typing import List, Dict
import random
import time

from gdpc import Block
from gdpc.geometry import placeCuboid

import city_simulator as city
from algoritmo_genetico import GenomaCiudad
from indirect_parametric_encoding import (
    crear_genoma_aleatorio,
    generar_paleta_edificio,
    crossover_genoma,
    mutar_genoma,
    setup as setup_encoding  # CAMBIADO: Importar setup en lugar de vocab
)
import numpy as np

from iga_logger import IGALogger

# ==============================
# Constantes configurables
# ==============================
TAMANO_POBLACION = 10
GENERACIONES_TOTALES = 200
INTERVALO_FEEDBACK = 10
PROB_MUTACION = 0.2
SIGMA_MUTACION = 0.1


# ==============================
# Función de limpieza
# ==============================
def limpiar_area_construccion(ciudad: GenomaCiudad):
    """Limpia el área de construcción en Minecraft"""
    for parcela in ciudad:
        placeCuboid(city.editor,
                    (parcela.x + city.buildArea.offset.x,
                     parcela.altura + 1,
                     parcela.y + city.buildArea.offset.z),
                    (parcela.x + city.buildArea.offset.x + parcela.ancho,
                     parcela.altura + 150,
                     parcela.y + city.buildArea.offset.z + parcela.alto),
                    Block("air")
                    )

        for i in range(parcela.ancho):
            for j in range(parcela.alto):
                city.editor.placeBlock(
                    (city.buildArea.offset.x + parcela.x + i, parcela.altura, city.buildArea.offset.z + parcela.y + j),
                    Block(city.blocks_values[parcela.x+i][parcela.y+j])
                )


# ==============================
# Construcción de ciudad con genoma estético
# ==============================
def construir_ciudad_con_genoma(ciudad: GenomaCiudad, genoma_estetico: Dict):
    """Construye una ciudad aplicando un genoma estético específico"""
    import grammar.grammar_entry_point
    grammar.grammar_entry_point.asignar_weights(genoma_estetico["enteros"])
    for i in range(len(ciudad)):
        parcela = ciudad[i]
        pos = (parcela.x, parcela.y)
        parcela.paleta = generar_paleta_edificio(
            pos=pos,
            genoma=genoma_estetico
        )
        parcela.construir()
        city.editor.flushBuffer()


# ==============================
# Popup de selección para torneos
# ==============================
class PopupTorneoEstetico:
    """Ventana modal para que el usuario elija entre dos genomas estéticos"""

    def __init__(self, parent, ciudad_base: GenomaCiudad,
                 genoma_a: Dict, genoma_b: Dict, generacion: int):
        self.ciudad_base = ciudad_base
        self.genoma_a = genoma_a
        self.genoma_b = genoma_b
        self.seleccion = None
        self.tiempo_inicio = None
        self.tiempo_decision = None

        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"Aesthetic Tournament - Generation {generacion}")
        self.ventana.geometry("700x350")
        self.ventana.resizable(False, False)

        self.ventana.transient(parent)
        self.ventana.grab_set()

        self._crear_interfaz(generacion)

        self.ventana.update_idletasks()
        x = (self.ventana.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.ventana.winfo_screenheight() // 2) - (350 // 2)
        self.ventana.geometry(f"700x350+{x}+{y}")

        self.tiempo_inicio = time.time()

    def _crear_interfaz(self, generacion):
        titulo = tk.Label(
            self.ventana,
            text=f"Generation {generacion} - Which city do you prefer?",
            font=("Arial", 16, "bold"),
            pady=20
        )
        titulo.pack()

        instrucciones = tk.Label(
            self.ventana,
            text="Build a city, then the other one, and compare",
            font=("Arial", 10),
            fg="#666"
        )
        instrucciones.pack()

        frame_genomas = tk.Frame(self.ventana)
        frame_genomas.pack(expand=True, fill="both", padx=20)

        # Frame A
        frame_a = tk.Frame(frame_genomas, relief="ridge", borderwidth=2, bg="#f0f0f0")
        frame_a.pack(side="left", expand=True, fill="both", padx=10)

        tk.Label(
            frame_a,
            text="City A",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        ).pack(pady=10)

        btn_construir_a = tk.Button(
            frame_a,
            text="🗂️ Build City A",
            command=lambda: self._cambiar_a_genoma(self.genoma_a),
            bg="#3498db",
            fg="white",
            font=("Arial", 11),
            padx=10,
            pady=8
        )
        btn_construir_a.pack(pady=5)

        self.btn_seleccionar_a = tk.Button(
            frame_a,
            text="✓ Select this style",
            command=lambda: self._seleccionar("A"),
            bg="#95a5a6",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=8
        )
        self.btn_seleccionar_a.pack(pady=5)

        # Frame B
        frame_b = tk.Frame(frame_genomas, relief="ridge", borderwidth=2, bg="#f0f0f0")
        frame_b.pack(side="right", expand=True, fill="both", padx=10)

        tk.Label(
            frame_b,
            text="City B",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        ).pack(pady=10)

        btn_construir_b = tk.Button(
            frame_b,
            text="🗂️ Build City B",
            command=lambda: self._cambiar_a_genoma(self.genoma_b),
            bg="#3498db",
            fg="white",
            font=("Arial", 11),
            padx=10,
            pady=8
        )
        btn_construir_b.pack(pady=5)

        self.btn_seleccionar_b = tk.Button(
            frame_b,
            text="✓ Select this style",
            command=lambda: self._seleccionar("B"),
            bg="#95a5a6",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=8
        )
        self.btn_seleccionar_b.pack(pady=5)

        # Botón confirmar
        frame_confirmar = tk.Frame(self.ventana)
        frame_confirmar.pack(pady=20)

        self.btn_confirmar = tk.Button(
            frame_confirmar,
            text="Confirm selection",
            command=self._confirmar,
            bg="#27ae60",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=30,
            pady=10,
            state="disabled"
        )
        self.btn_confirmar.pack()

    def _cambiar_a_genoma(self, genoma: Dict):
        try:
            limpiar_area_construccion(self.ciudad_base)
            construir_ciudad_con_genoma(self.ciudad_base, genoma)
            messagebox.showinfo("Construction", "City built. Watch and compare.")
        except Exception as e:
            messagebox.showerror("Error", f"Error while building: {str(e)}")

    def _seleccionar(self, opcion: str):
        self.seleccion = opcion

        if opcion == "A":
            self.btn_seleccionar_a.config(bg="#27ae60")
            self.btn_seleccionar_b.config(bg="#95a5a6")
        else:
            self.btn_seleccionar_a.config(bg="#95a5a6")
            self.btn_seleccionar_b.config(bg="#27ae60")

        self.btn_confirmar.config(state="normal")

    def _confirmar(self):
        if self.seleccion is None:
            messagebox.showwarning("Warning", "You must choose a city first")
            return

        if self.tiempo_inicio is not None:
            self.tiempo_decision = time.time() - self.tiempo_inicio

        self.ventana.destroy()

    def obtener_seleccion(self):
        self.ventana.wait_window()
        genoma_elegido = self.genoma_a if self.seleccion == "A" else self.genoma_b
        seleccion_str = self.seleccion if self.seleccion else "A"
        return genoma_elegido, seleccion_str, self.tiempo_decision


# ==============================
# Funciones para manejar los 8 enteros
# ==============================
def crear_genoma_con_enteros():
    """Crea un genoma aleatorio que incluye los 8 enteros"""
    genoma = crear_genoma_aleatorio()
    genoma["enteros"] = np.array([random.randint(0, 20) for _ in range(8)])
    return genoma


def crossover_genoma_con_enteros(padre1: Dict, padre2: Dict):
    """Crossover que incluye los 8 enteros"""
    hijo1, hijo2 = crossover_genoma(padre1, padre2)

    enteros1 = []
    enteros2 = []

    for i in range(8):
        if random.randint(0, 1) == 0:
            enteros1.append(padre1["enteros"][i])
            enteros2.append(padre2["enteros"][i])
        else:
            enteros1.append(padre2["enteros"][i])
            enteros2.append(padre1["enteros"][i])

    hijo1["enteros"] = np.array(enteros1)
    hijo2["enteros"] = np.array(enteros2)

    return hijo1, hijo2


def mutar_genoma_con_enteros(genoma: Dict, prob_mutacion: float = 0.2, sigma: float = 0.1):
    """Mutación que incluye los 8 enteros"""
    genoma = mutar_genoma(genoma, prob_mutacion, sigma)

    for i in range(8):
        if random.random() < 0.2:
            cambio = random.randint(-1, 1)
            genoma["enteros"][i] = max(0, genoma["enteros"][i] + cambio)

    return genoma


# ==============================
# Generación de descendientes
# ==============================
def generar_descendientes(genoma_padre: Dict, n_descendientes: int) -> List[Dict]:
    """Genera n descendientes a partir de un genoma padre mediante mutación"""
    descendientes = []

    for _ in range(n_descendientes):
        hijo = {
            "base_vector": genoma_padre["base_vector"].copy(),
            "amplitude": genoma_padre["amplitude"].copy(),
            "spatial": {k: v.copy() if hasattr(v, 'copy') else v
                        for k, v in genoma_padre["spatial"].items()},
            "slot_offsets": {k: v.copy() for k, v in genoma_padre["slot_offsets"].items()},
            "distance_weights": genoma_padre["distance_weights"].copy(),
            "enteros": genoma_padre["enteros"].copy()
        }

        hijo = mutar_genoma_con_enteros(hijo, prob_mutacion=PROB_MUTACION, sigma=SIGMA_MUTACION)
        descendientes.append(hijo)

    return descendientes


def generar_siguiente_generacion(poblacion: List[Dict], preservar_mejor: bool = False,
                                 mejor_individuo: Dict = None) -> List[Dict]:
    """Genera la siguiente generación mediante crossover y mutación"""
    nueva_poblacion = []

    if preservar_mejor and mejor_individuo is not None:
        nueva_poblacion.append(mejor_individuo)

    while len(nueva_poblacion) < TAMANO_POBLACION:
        padre1, padre2 = random.sample(poblacion, 2)
        hijo1, hijo2 = crossover_genoma_con_enteros(padre1, padre2)
        hijo1 = mutar_genoma_con_enteros(hijo1, prob_mutacion=PROB_MUTACION, sigma=SIGMA_MUTACION)
        hijo2 = mutar_genoma_con_enteros(hijo2, prob_mutacion=PROB_MUTACION, sigma=SIGMA_MUTACION)

        nueva_poblacion.append(hijo1)
        if len(nueva_poblacion) < TAMANO_POBLACION:
            nueva_poblacion.append(hijo2)

    return nueva_poblacion


# ==============================
# Algoritmo evolutivo interactivo principal
# ==============================
def ejecutar_iga_estetico(root_window, ciudad_funcional: GenomaCiudad):
    """
    Ejecuta el algoritmo genético interactivo para evolucionar la estética de la ciudad.
    """
    print("\n" + "=" * 60)
    print("🎨 INICIANDO ALGORITMO GENÉTICO INTERACTIVO ESTÉTICO")
    print("=" * 60)

    # NUEVO: Inicializar encoding y obtener vocab
    print("\n📚 Inicializando sistema de encoding...")
    vocab_obj, embeddings_obj = setup_encoding()

    # Inicializar logger CON VOCABULARIO
    logger = IGALogger(nombre_experimento="IGA_Aesthetic", vocab=vocab_obj)
    tiempo_inicio_total = time.time()

    # Generar población inicial aleatoria
    print(f"\n📊 Generando población inicial ({TAMANO_POBLACION} individuos)...")
    poblacion = [crear_genoma_con_enteros() for _ in range(TAMANO_POBLACION)]

    genoma_ganador = None

    # Evolución
    for gen in range(GENERACIONES_TOTALES):
        es_generacion_feedback = (gen % INTERVALO_FEEDBACK == 0)
        es_primera_generacion_post_feedback = (gen % INTERVALO_FEEDBACK == 1) and gen > 0

        if es_generacion_feedback:
            print(f"\n🎯 GENERACIÓN {gen} (CON FEEDBACK)")

            genoma_a, genoma_b = random.sample(poblacion, 2)

            popup = PopupTorneoEstetico(
                parent=root_window,
                ciudad_base=ciudad_funcional,
                genoma_a=genoma_a,
                genoma_b=genoma_b,
                generacion=gen
            )

            genoma_ganador, seleccion, tiempo_decision = popup.obtener_seleccion()
            print(f"   ✓ Usuario seleccionó: {seleccion} (en {tiempo_decision:.1f}s)")

            # Determinar el perdedor
            genoma_perdedor = genoma_b if seleccion == "A" else genoma_a

            # Registrar con GANADOR Y PERDEDOR
            logger.registrar_generacion(
                gen=gen,
                es_feedback=True,
                poblacion=poblacion,
                ganador=genoma_ganador,
                perdedor=genoma_perdedor,  # NUEVO
                seleccion_usuario=seleccion,
                tiempo_decision=tiempo_decision
            )

            print(f"   📈 Generando 8 descendientes + 2 aleatorios...")
            poblacion = generar_descendientes(genoma_ganador, 9)
            # poblacion.append(crear_genoma_con_enteros())
            poblacion.append(crear_genoma_con_enteros())

        elif es_primera_generacion_post_feedback:
            print(f"\n🔄 GENERATION {gen} (post-feedback - adding 1 random)")

            nueva_poblacion = generar_siguiente_generacion(
                poblacion,
                preservar_mejor=True,
                mejor_individuo=genoma_ganador
            )

            nueva_poblacion[-1] = crear_genoma_con_enteros()
            nueva_poblacion[-2] = crear_genoma_con_enteros()

            poblacion = nueva_poblacion

            logger.registrar_generacion(
                gen=gen,
                es_feedback=False,
                poblacion=poblacion,
                ganador=genoma_ganador
            )

        else:
            print(f"\n🔄 GENERACIÓN {gen} (sin feedback - exploración local)")

            poblacion = generar_siguiente_generacion(
                poblacion,
                preservar_mejor=True,
                mejor_individuo=genoma_ganador
            )

            logger.registrar_generacion(
                gen=gen,
                es_feedback=False,
                poblacion=poblacion,
                ganador=genoma_ganador
            )

    print("\n" + "=" * 60)
    print("✅ ALGORITMO GENÉTICO INTERACTIVO COMPLETADO")
    print("=" * 60)

    # Torneo final
    if genoma_ganador is None or (GENERACIONES_TOTALES - 1) % INTERVALO_FEEDBACK != 0:
        print("\n🏆 TORNEO FINAL")
        genoma_a, genoma_b = random.sample(poblacion, 2)

        popup = PopupTorneoEstetico(
            parent=root_window,
            ciudad_base=ciudad_funcional,
            genoma_a=genoma_a,
            genoma_b=genoma_b,
            generacion=GENERACIONES_TOTALES
        )

        genoma_ganador, seleccion, tiempo_decision = popup.obtener_seleccion()

        # Determinar perdedor del torneo final
        genoma_perdedor = genoma_b if seleccion == "A" else genoma_a

        logger.registrar_generacion(
            gen=GENERACIONES_TOTALES,
            es_feedback=True,
            poblacion=poblacion,
            ganador=genoma_ganador,
            perdedor=genoma_perdedor,
            seleccion_usuario=seleccion,
            tiempo_decision=tiempo_decision
        )

    print("\n🏗️ Construyendo ciudad ganadora final...")
    limpiar_area_construccion(ciudad_funcional)
    construir_ciudad_con_genoma(ciudad_funcional, genoma_ganador)
    print("   ✓ Ciudad final construida")
    # Finalizar logging
    tiempo_total = time.time() - tiempo_inicio_total
    logger.finalizar(genoma_ganador, tiempo_total)

    return genoma_ganador


# ==============================
# Función de integración con el flujo principal
# ==============================
def ejecutar_pipeline_completo(root_window, ciudad_funcional: GenomaCiudad):
    """Ejecuta el pipeline completo: optimización funcional + optimización estética"""
    print("\n🏙️ FASE 1: Optimización funcional completada")
    print(f"   Ciudad con {len(ciudad_funcional)} parcelas")
    print("   Parcelas determinadas: posición, tamaño, puertas, terreno nivelado")

    print("\n🎨 FASE 2: Optimización estética interactiva")
    genoma_final = ejecutar_iga_estetico(root_window, ciudad_funcional)

    messagebox.showinfo(
        "¡Completado!",
        "Ciudad óptima construida con éxito.\n"
        f"Total de generaciones: {GENERACIONES_TOTALES}\n"
        f"Feedback del usuario: {GENERACIONES_TOTALES // INTERVALO_FEEDBACK} veces"
    )

    return genoma_final