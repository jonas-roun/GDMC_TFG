import tkinter as tk
from tkinter import messagebox
from typing import List, Dict
import random

from gdpc import Block
from gdpc.geometry import placeCuboid

import city_simulator as city
from algoritmo_genetico import GenomaCiudad
from indirect_parametric_encoding import (
    crear_genoma_aleatorio,
    generar_paleta_edificio,
    crossover_genoma,
    mutar_genoma
)

# ==============================
# Constantes configurables
# ==============================
TAMANO_POBLACION = 10
GENERACIONES_TOTALES = 200
INTERVALO_FEEDBACK = 10  # Cada cuántas generaciones se pide feedback
PROB_MUTACION = 0.2
SIGMA_MUTACION = 0.1


# ==============================
# Función de limpieza (implementar según tu sistema)
# ==============================
def limpiar_area_construccion(ciudad: GenomaCiudad):
    """
    Limpia el área de construcción en Minecraft correspondiente a las parcelas de la ciudad.

    Args:
        ciudad: Lista de parcelas cuyas áreas deben ser limpiadas
    """
    # Ejemplo de implementación:
    for parcela in ciudad:
        placeCuboid(city.editor,
            (parcela.x  + city.buildArea.offset.x,
             parcela.altura+1,
             parcela.y  + city.buildArea.offset.z),
            (parcela.x + city.buildArea.offset.x+parcela.ancho,
             parcela.altura+150,
             parcela.y + city.buildArea.offset.z+parcela.alto),
            Block("air")
        )
    city.editor.flushBuffer()


# ==============================
# Construcción de ciudad con genoma estético
# ==============================
def construir_ciudad_con_genoma(ciudad: GenomaCiudad, genoma_estetico: Dict):
    """
    Construye una ciudad aplicando un genoma estético específico.

    Las parcelas ya están completamente determinadas (posición, tamaño, puerta,
    terreno nivelado) por el AG funcional. Solo se aplican las paletas de materiales.

    Args:
        ciudad: Lista de parcelas (GenomaCiudad) ya optimizada funcionalmente
        genoma_estetico: Genoma del indirect parametric encoding
    """
    for i in range(len(ciudad)):
        parcela = ciudad[i]

        # Aplicar genoma estético para generar paleta
        pos = (parcela.x, parcela.y)
        parcela.paleta = generar_paleta_edificio(
            pos=pos,
            genoma=genoma_estetico
        )

        # Construir con la nueva paleta
        parcela.construir()
        city.editor.flushBuffer()


# ==============================
# Popup de selección para torneos
# ==============================
class PopupTorneoEstetico:
    """
    Ventana modal para que el usuario elija entre dos genomas estéticos.
    """

    def __init__(self, parent, ciudad_base: GenomaCiudad,
                 genoma_a: Dict, genoma_b: Dict, generacion: int):
        """
        Args:
            parent: Ventana padre de Tkinter
            ciudad_base: Ciudad funcional base (mismas parcelas para ambos)
            genoma_a, genoma_b: Los dos genomas estéticos a comparar
            generacion: Número de generación actual
        """
        self.ciudad_base = ciudad_base
        self.genoma_a = genoma_a
        self.genoma_b = genoma_b
        self.seleccion = None  # None, "A" o "B"

        # Crear ventana modal
        self.ventana = tk.Toplevel(parent)
        self.ventana.title(f"Torneo Estético - Generación {generacion}")
        self.ventana.geometry("700x350")
        self.ventana.resizable(False, False)

        # Hacer modal
        self.ventana.transient(parent)
        self.ventana.grab_set()

        self._crear_interfaz(generacion)

        # Centrar ventana
        self.ventana.update_idletasks()
        x = (self.ventana.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.ventana.winfo_screenheight() // 2) - (350 // 2)
        self.ventana.geometry(f"700x350+{x}+{y}")

    def _crear_interfaz(self, generacion):
        # Título superior
        titulo = tk.Label(
            self.ventana,
            text=f"Generación {generacion} - ¿Qué estilo te gusta más?",
            font=("Arial", 16, "bold"),
            pady=20
        )
        titulo.pack()

        # Instrucciones
        instrucciones = tk.Label(
            self.ventana,
            text="Construye un estilo, luego cambia al otro para comparar",
            font=("Arial", 10),
            fg="#666"
        )
        instrucciones.pack()

        # Frame con las dos columnas
        frame_genomas = tk.Frame(self.ventana)
        frame_genomas.pack(expand=True, fill="both", padx=20)

        # ---------- GENOMA A (Izquierda) ----------
        frame_a = tk.Frame(frame_genomas, relief="ridge", borderwidth=2, bg="#f0f0f0")
        frame_a.pack(side="left", expand=True, fill="both", padx=10)

        tk.Label(
            frame_a,
            text="Estilo A",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        ).pack(pady=10)

        # Botón construir A
        btn_construir_a = tk.Button(
            frame_a,
            text="🏗️ Mostrar Estilo A",
            command=lambda: self._cambiar_a_genoma(self.genoma_a),
            bg="#3498db",
            fg="white",
            font=("Arial", 11),
            padx=10,
            pady=8
        )
        btn_construir_a.pack(pady=5)

        # Botón seleccionar A
        self.btn_seleccionar_a = tk.Button(
            frame_a,
            text="✓ Seleccionar este estilo",
            command=lambda: self._seleccionar("A"),
            bg="#95a5a6",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=8
        )
        self.btn_seleccionar_a.pack(pady=5)

        # ---------- GENOMA B (Derecha) ----------
        frame_b = tk.Frame(frame_genomas, relief="ridge", borderwidth=2, bg="#f0f0f0")
        frame_b.pack(side="right", expand=True, fill="both", padx=10)

        tk.Label(
            frame_b,
            text="Estilo B",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        ).pack(pady=10)

        # Botón construir B
        btn_construir_b = tk.Button(
            frame_b,
            text="🏗️ Mostrar Estilo B",
            command=lambda: self._cambiar_a_genoma(self.genoma_b),
            bg="#3498db",
            fg="white",
            font=("Arial", 11),
            padx=10,
            pady=8
        )
        btn_construir_b.pack(pady=5)

        # Botón seleccionar B
        self.btn_seleccionar_b = tk.Button(
            frame_b,
            text="✓ Seleccionar este estilo",
            command=lambda: self._seleccionar("B"),
            bg="#95a5a6",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=8
        )
        self.btn_seleccionar_b.pack(pady=5)

        # Botón confirmar (centro abajo)
        frame_confirmar = tk.Frame(self.ventana)
        frame_confirmar.pack(pady=20)

        self.btn_confirmar = tk.Button(
            frame_confirmar,
            text="Confirmar Selección",
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
        """
        Cambia al estilo especificado: limpia la ciudad actual y construye la nueva.
        Las parcelas son las mismas, solo cambia la estética.
        """
        try:
            limpiar_area_construccion(self.ciudad_base)
            construir_ciudad_con_genoma(self.ciudad_base, genoma)
            messagebox.showinfo("Construcción", "Estilo construido. Observa y compara.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al construir: {str(e)}")

    def _seleccionar(self, opcion: str):
        """Marca la selección y actualiza la UI"""
        self.seleccion = opcion

        # Actualizar colores de botones
        if opcion == "A":
            self.btn_seleccionar_a.config(bg="#27ae60")  # Verde
            self.btn_seleccionar_b.config(bg="#95a5a6")  # Gris
        else:
            self.btn_seleccionar_a.config(bg="#95a5a6")  # Gris
            self.btn_seleccionar_b.config(bg="#27ae60")  # Verde

        # Habilitar botón confirmar
        self.btn_confirmar.config(state="normal")

    def _confirmar(self):
        """Cierra el popup y devuelve la selección"""
        if self.seleccion is None:
            messagebox.showwarning("Advertencia", "Debes seleccionar un estilo primero")
            return

        self.ventana.destroy()

    def obtener_seleccion(self) -> Dict:
        """
        Muestra el popup y espera a que el usuario seleccione.
        Retorna el genoma seleccionado.
        """
        self.ventana.wait_window()

        if self.seleccion == "A":
            return self.genoma_a
        elif self.seleccion == "B":
            return self.genoma_b
        else:
            # Por defecto, devolver genoma A
            return self.genoma_a


# ==============================
# Generación de descendientes
# ==============================
def generar_descendientes(genoma_padre: Dict, n_descendientes: int) -> List[Dict]:
    """
    Genera n descendientes a partir de un genoma padre mediante mutación.

    Args:
        genoma_padre: Genoma base
        n_descendientes: Número de descendientes a generar

    Returns:
        Lista de genomas descendientes
    """
    descendientes = []

    for _ in range(n_descendientes):
        # Crear copia profunda del genoma padre
        hijo = {
            "base_vector": genoma_padre["base_vector"].copy(),
            "amplitude": genoma_padre["amplitude"].copy(),
            "spatial": {k: v.copy() if hasattr(v, 'copy') else v
                        for k, v in genoma_padre["spatial"].items()},
            "slot_offsets": {k: v.copy() for k, v in genoma_padre["slot_offsets"].items()},
            "distance_weights": genoma_padre["distance_weights"].copy()
        }

        # Mutar
        hijo = mutar_genoma(hijo, prob_mutacion=PROB_MUTACION, sigma=SIGMA_MUTACION)
        descendientes.append(hijo)

    return descendientes


def generar_siguiente_generacion(poblacion: List[Dict]) -> List[Dict]:
    """
    Genera la siguiente generación mediante crossover y mutación de la población actual.

    Args:
        poblacion: Población actual de genomas

    Returns:
        Nueva población del mismo tamaño
    """
    nueva_poblacion = []

    # Generar pares de hijos mediante crossover
    while len(nueva_poblacion) < TAMANO_POBLACION - 1:  # -1 para dejar espacio al aleatorio
        # Seleccionar dos padres aleatorios
        padre1, padre2 = random.sample(poblacion, 2)

        # Crossover
        hijo1, hijo2 = crossover_genoma(padre1, padre2)

        # Mutar
        hijo1 = mutar_genoma(hijo1, prob_mutacion=PROB_MUTACION, sigma=SIGMA_MUTACION)
        hijo2 = mutar_genoma(hijo2, prob_mutacion=PROB_MUTACION, sigma=SIGMA_MUTACION)

        nueva_poblacion.append(hijo1)
        if len(nueva_poblacion) < TAMANO_POBLACION - 1:
            nueva_poblacion.append(hijo2)

    # Añadir un genoma completamente aleatorio para mantener diversidad
    nueva_poblacion.append(crear_genoma_aleatorio())

    return nueva_poblacion


# ==============================
# Algoritmo evolutivo interactivo principal
# ==============================
def ejecutar_iga_estetico(root_window, ciudad_funcional: GenomaCiudad):
    """
    Ejecuta el algoritmo genético interactivo para evolucionar la estética de la ciudad.

    Args:
        root_window: Ventana principal de Tkinter
        ciudad_funcional: Ciudad ya optimizada funcionalmente (distribución de parcelas)

    Returns:
        Genoma estético final elegido
    """
    print("\n" + "=" * 60)
    print("🎨 INICIANDO ALGORITMO GENÉTICO INTERACTIVO ESTÉTICO")
    print("=" * 60)

    # Generar población inicial aleatoria
    print(f"\n📊 Generando población inicial ({TAMANO_POBLACION} individuos)...")
    poblacion = [crear_genoma_aleatorio() for _ in range(TAMANO_POBLACION)]

    # Genoma ganador actual (se actualiza en cada generación con feedback)
    genoma_ganador = None

    # Evolución
    for gen in range(GENERACIONES_TOTALES):
        es_generacion_feedback = (gen % INTERVALO_FEEDBACK == 0)

        if es_generacion_feedback:
            print(f"\n🎯 GENERACIÓN {gen} (CON FEEDBACK)")

            # Seleccionar dos individuos aleatorios para torneo
            genoma_a, genoma_b = random.sample(poblacion, 2)

            # Mostrar popup y esperar decisión del usuario
            popup = PopupTorneoEstetico(
                parent=root_window,
                ciudad_base=ciudad_funcional,
                genoma_a=genoma_a,
                genoma_b=genoma_b,
                generacion=gen
            )

            genoma_ganador = popup.obtener_seleccion()
            print(f"   ✓ Usuario seleccionó un genoma")

            # Generar 9 descendientes del ganador + 1 aleatorio para la siguiente generación
            print(f"   📈 Generando {TAMANO_POBLACION - 1} descendientes...")
            poblacion = generar_descendientes(genoma_ganador, TAMANO_POBLACION - 1)
            poblacion.append(crear_genoma_aleatorio())  # Diversidad

        else:
            print(f"\n🔄 GENERACIÓN {gen} (sin feedback - exploración local)")

            # Generar siguiente generación mediante crossover y mutación
            poblacion = generar_siguiente_generacion(poblacion)

    print("\n" + "=" * 60)
    print("✅ ALGORITMO GENÉTICO INTERACTIVO COMPLETADO")
    print("=" * 60)

    # Última selección del usuario (torneo final si no terminó en generación con feedback)
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

        genoma_ganador = popup.obtener_seleccion()

    return genoma_ganador


# ==============================
# Función de integración con el flujo principal
# ==============================
def ejecutar_pipeline_completo(root_window, ciudad_funcional: GenomaCiudad):
    """
    Ejecuta el pipeline completo: optimización funcional + optimización estética.

    Esta función asume que ciudad_funcional ya fue optimizada mediante el GA funcional,
    con todas las parcelas determinadas (posición, tamaño, puertas) y el terreno nivelado.

    Args:
        root_window: Ventana principal de Tkinter
        ciudad_funcional: Ciudad optimizada funcionalmente con terreno nivelado
    """
    print("\n🏙️ FASE 1: Optimización funcional completada")
    print(f"   Ciudad con {len(ciudad_funcional)} parcelas")
    print("   Parcelas determinadas: posición, tamaño, puertas, terreno nivelado")

    print("\n🎨 FASE 2: Optimización estética interactiva")
    genoma_final = ejecutar_iga_estetico(root_window, ciudad_funcional)

    print("\n🏗️ FASE 3: Construcción de ciudad final")
    limpiar_area_construccion(ciudad_funcional)
    construir_ciudad_con_genoma(ciudad_funcional, genoma_final)

    messagebox.showinfo(
        "¡Completado!",
        "Ciudad óptima construida con éxito.\n"
        f"Total de generaciones: {GENERACIONES_TOTALES}\n"
        f"Feedback del usuario: {GENERACIONES_TOTALES // INTERVALO_FEEDBACK} veces"
    )

    return genoma_final