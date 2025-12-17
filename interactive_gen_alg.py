import tkinter as tk
from random import random
from tkinter import messagebox
from typing import List, Callable

from algoritmo_genetico import generar_ciudad
from urbanismo.parcela import Parcela

GenomaCiudad = List[Parcela]


def simular_evolucion_estetica_torneo(root_window, poblacion_inicial, generaciones=20):
    """
    root_window: la ventana principal de Tkinter (tu root actual)
    """
    poblacion = poblacion_inicial

    for gen in range(generaciones):
        print(f"🎨 Generación estética {gen}")

        ganadores = []

        # Torneo 1v1
        while len(ganadores) < len(poblacion) // 2:
            # Seleccionar dos ciudades aleatorias
            ciudad_a, ciudad_b = random.sample(poblacion, 2)

            # Mostrar popup y esperar decisión del usuario
            popup = PopupSeleccionCiudad(
                parent=root_window,
                ciudad_a=ciudad_a,
                ciudad_b=ciudad_b,
                callback_construir=construir_ciudad_en_minecraft
            )

            ganadora = popup.obtener_seleccion()
            ganadores.append(ganadora)

        # Generar siguiente generación (crossover + mutación)
        nueva_poblacion = ganadores.copy()

        while len(nueva_poblacion) < len(poblacion):
            padre1, padre2 = random.sample(ganadores, 2)
            hijo = crossover_estetico(padre1, padre2)
            hijo = mutar_estetico(hijo)
            nueva_poblacion.append(hijo)

        poblacion = nueva_poblacion

    # Torneo final
    return torneo_final(root_window, poblacion)


def ejecutar_iga_estetico(root_window):
    """Ejecuta el IGA estético después de tener ciudades funcionales"""

    # Paso 1: Ejecutar GA funcional (tu código actual)
    print("🏗️ FASE 1: Optimización funcional...")
    ag.numero_de_parcelas = 10
    poblacion_funcional, _ = generar_ciudad(10, 50)

    # Paso 2: Tomar las mejores ciudades
    ciudades_para_iga = poblacion_funcional[:6]  # Top 6

    # Paso 3: Inicializar paletas y gramáticas
    for ciudad in ciudades_para_iga:
        for parcela in ciudad:
            parcela.paleta_bloques = generar_paleta_aleatoria()
            parcela.pesos_gramatica = generar_pesos_aleatorios()

    # Paso 4: Ejecutar IGA
    print("🎨 FASE 2: Optimización estética...")
    ciudad_final = simular_evolucion_estetica_torneo(
        root_window=root_window,
        poblacion_inicial=ciudades_para_iga,
        generaciones=10
    )

    # Paso 5: Construir ciudad final
    messagebox.showinfo("Finalizado", "¡Ciudad óptima encontrada!")
    construir_ciudad_completa(ciudad_final)


def construir_ciudad_en_minecraft(ciudad: GenomaCiudad, lado: str):
    """
    Construye la ciudad en Minecraft.
    lado: "izquierda" o "derecha" para posicionar las ciudades lado a lado.
    """
    offset_x = 0 if lado == "izquierda" else 200  # Separar 200 bloques

    for parcela in ciudad:
        # Ajustar posición según el lado
        parcela_temp = parcela.copy()
        parcela_temp.x += offset_x

        # Construir la parcela
        parcela_temp.level_plot()
        parcela_temp.construir()
        city.editor.flushBuffer()

class PopupSeleccionCiudad:
    def __init__(self, parent, ciudad_a: GenomaCiudad, ciudad_b: GenomaCiudad,
                 callback_construir: Callable[[GenomaCiudad, str], None]):
        """
        parent: ventana padre de Tkinter
        ciudad_a, ciudad_b: las dos ciudades a comparar
        callback_construir: función que construye la ciudad en Minecraft
                           Firma: callback_construir(ciudad, lado) donde lado = "izquierda" | "derecha"
        """
        self.ciudad_a = ciudad_a
        self.ciudad_b = ciudad_b
        self.callback_construir = callback_construir
        self.seleccion = None  # None, "A" o "B"

        # Crear ventana modal
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Selección de Ciudad - Torneo Estético")
        self.ventana.geometry("600x300")
        self.ventana.resizable(False, False)

        # Hacer modal (bloquea interacción con ventana padre)
        self.ventana.transient(parent)
        self.ventana.grab_set()

        self._crear_interfaz()

        # Centrar ventana
        self.ventana.update_idletasks()
        x = (self.ventana.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.ventana.winfo_screenheight() // 2) - (300 // 2)
        self.ventana.geometry(f"600x300+{x}+{y}")

    def _crear_interfaz(self):
        # ========================================
        # Título superior
        # ========================================
        titulo = tk.Label(
            self.ventana,
            text="¿Qué ciudad te gusta más?",
            font=("Arial", 16, "bold"),
            pady=20
        )
        titulo.pack()

        # ========================================
        # Frame con las dos columnas
        # ========================================
        frame_ciudades = tk.Frame(self.ventana)
        frame_ciudades.pack(expand=True, fill="both", padx=20)

        # ---------- CIUDAD A (Izquierda) ----------
        frame_a = tk.Frame(frame_ciudades, relief="ridge", borderwidth=2)
        frame_a.pack(side="left", expand=True, fill="both", padx=10)

        tk.Label(
            frame_a,
            text="Ciudad A",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        # Botón construir A
        btn_construir_a = tk.Button(
            frame_a,
            text="🏗️ Construir en Minecraft",
            command=lambda: self._construir_ciudad(self.ciudad_a, "izquierda"),
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
            text="✓ Seleccionar esta",
            command=lambda: self._seleccionar("A"),
            bg="#95a5a6",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=8
        )
        self.btn_seleccionar_a.pack(pady=5)

        # ---------- CIUDAD B (Derecha) ----------
        frame_b = tk.Frame(frame_ciudades, relief="ridge", borderwidth=2)
        frame_b.pack(side="right", expand=True, fill="both", padx=10)

        tk.Label(
            frame_b,
            text="Ciudad B",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        # Botón construir B
        btn_construir_b = tk.Button(
            frame_b,
            text="🏗️ Construir en Minecraft",
            command=lambda: self._construir_ciudad(self.ciudad_b, "derecha"),
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
            text="✓ Seleccionar esta",
            command=lambda: self._seleccionar("B"),
            bg="#95a5a6",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=8
        )
        self.btn_seleccionar_b.pack(pady=5)

        # ========================================
        # Botón confirmar (centro abajo)
        # ========================================
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
            state="disabled"  # Deshabilitado hasta que se seleccione
        )
        self.btn_confirmar.pack()

    def _construir_ciudad(self, ciudad: GenomaCiudad, lado: str):
        """Llama al callback para construir la ciudad en Minecraft"""
        try:
            self.callback_construir(ciudad, lado)
            messagebox.showinfo("Construcción", f"Ciudad construida en el lado {lado}")
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
            messagebox.showwarning("Advertencia", "Debes seleccionar una ciudad primero")
            return

        self.ventana.destroy()

    def obtener_seleccion(self) -> GenomaCiudad:
        """
        Muestra el popup y espera a que el usuario seleccione.
        Retorna la ciudad seleccionada.
        """
        self.ventana.wait_window()  # Bloquea hasta que se cierre la ventana

        if self.seleccion == "A":
            return self.ciudad_a
        elif self.seleccion == "B":
            return self.ciudad_b
        else:
            # Si se cierra sin seleccionar, devolver ciudad A por defecto
            return self.ciudad_a