"""
Sistema de logging completo para el Algoritmo Genético Interactivo.
Genera logs detallados en CSV y PDF con gráficos de evolución y análisis de coherencia.

PARTE 1 de 2: Clase IGALogger con métodos de análisis
PARTE 2 de 2: Métodos de generación de PDF
"""

import os
import csv
import json
from datetime import datetime
from typing import List, Dict, Any
import numpy as np

# Importaciones condicionales para PDF
try:
    from matplotlib import pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ Matplotlib no disponible - No se generarán PDFs con gráficos")


class IGALogger:
    """
    Logger completo para el Algoritmo Genético Interactivo.
    Registra toda la evolución y genera informes visuales con análisis de coherencia.
    """

    def __init__(self, nombre_experimento: str = "IGA_Experiment", vocab=None):
        """
        Inicializa el logger y crea la carpeta de salida.

        Args:
            nombre_experimento: Nombre base del experimento
            vocab: VocabularyBuilder para análisis dimensional
        """
        # Crear carpeta con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.carpeta = f"logs/{nombre_experimento}_{timestamp}"
        os.makedirs(self.carpeta, exist_ok=True)

        # Archivos de salida
        self.csv_path = os.path.join(self.carpeta, "evolucion.csv")
        self.json_path = os.path.join(self.carpeta, "resumen.json")
        self.pdf_path = os.path.join(self.carpeta, "graficos.pdf")

        # Vocabulario para análisis dimensional
        self.vocab = vocab

        # Máscaras de índices para base_vector
        if vocab:
            self._calcular_mascaras_indices()

        # Datos recopilados
        self.generaciones = []
        self.vectores_preferencia = []  # Para análisis de coherencia

        self.metadata = {
            "timestamp": timestamp,
            "experimento": nombre_experimento,
            "inicio": datetime.now().isoformat()
        }

        print(f"📊 Logger inicializado: {self.carpeta}")

    def _calcular_mascaras_indices(self):
        """Calcula máscaras de índices para las secciones del base_vector"""
        v = self.vocab

        self.color_mask = slice(0, v.n_color)

        offset = v.n_color
        self.material_mask = slice(offset, offset + v.n_material)

        offset += v.n_material
        self.categories_mask = slice(offset, offset + v.n_categories)

        offset += v.n_categories
        self.processing_mask = slice(offset, offset + v.n_processing)

        offset += v.n_processing
        # self.biome_mask ELIMINADO - biome no se usa

        # Nombres de slots (10 slots - accent eliminado)
        self.slot_names = ["primary", "floor", "ceiling", "roof",
                          "window", "stairs", "light", "fence", "gate", "door"]

    def registrar_generacion(self,
                            gen: int,
                            es_feedback: bool,
                            poblacion: List[Dict],
                            ganador: Dict = None,
                            perdedor: Dict = None,
                            seleccion_usuario: str = None,
                            tiempo_decision: float = None):
        """
        Registra información de una generación.

        Args:
            gen: Número de generación
            es_feedback: Si hubo feedback del usuario
            poblacion: Población actual (lista de genomas)
            ganador: Genoma ganador (si aplica)
            perdedor: Genoma perdedor (si aplica)
            seleccion_usuario: "A" o "B" (si aplica)
            tiempo_decision: Time que tardó el usuario en decidir (seconds)
        """
        # Calcular métricas de diversidad
        diversidad = self._calcular_diversidad(poblacion)

        # Métricas de los enteros
        stats_enteros = self._calcular_stats_enteros(poblacion)

        # Métricas de distance_weights
        stats_weights = self._calcular_stats_weights(poblacion)

        # Registro de la generación
        registro = {
            "generacion": gen,
            "es_feedback": es_feedback,
            "timestamp": datetime.now().isoformat(),

            # Diversidad
            "diversidad_base_vector": diversidad["base_vector"],
            "diversidad_amplitude": diversidad["amplitude"],
            "diversidad_distance_weights": diversidad["distance_weights"],
            "diversidad_enteros": diversidad["enteros"],

            # Estadísticas de enteros (media y std de cada uno)
            **{f"entero_{i}_mean": stats_enteros["means"][i] for i in range(8)},
            **{f"entero_{i}_std": stats_enteros["stds"][i] for i in range(8)},

            # Estadísticas de distance_weights (SIN BIOME - solo 4)
            **{f"weight_{i}_mean": stats_weights["means"][i] for i in range(4)},
            **{f"weight_{i}_std": stats_weights["stds"][i] for i in range(4)},

            # Información de feedback
            "seleccion_usuario": seleccion_usuario if es_feedback else None,
            "tiempo_decision_s": tiempo_decision if es_feedback else None,
        }

        # ANÁLISIS DE COHERENCIA si hay feedback
        if es_feedback and ganador is not None and perdedor is not None:
            analisis_decision = self._analizar_decision(ganador, perdedor)
            registro["analisis_decision"] = analisis_decision

            # Guardar vector de preferencia para análisis temporal
            self.vectores_preferencia.append(analisis_decision["vector_preferencia"])

        # Guardar genoma ganador si existe
        if ganador is not None:
            registro["ganador_enteros"] = ganador["enteros"].tolist()
            registro["ganador_distance_weights"] = ganador["distance_weights"].tolist()

        self.generaciones.append(registro)

        # Escribir en CSV inmediatamente (para no perder datos)
        self._escribir_csv()

    # ========================================================================
    # MÉTODOS DE ANÁLISIS DE COHERENCIA
    # ========================================================================

    def _analizar_decision(self, ganador: Dict, perdedor: Dict) -> Dict:
        """
        Analiza una decisión del usuario: ganador vs perdedor.
        Calcula vector de preferencia y diferencias significativas.
        """
        analisis = {}

        # 1. Vector de preferencia
        vector_pref = self._calcular_vector_preferencia(ganador, perdedor)
        analisis["vector_preferencia"] = vector_pref

        # 2. Coherencia local
        if len(self.vectores_preferencia) > 0:
            coherencia_local = self._calcular_coherencia_local(vector_pref)
            analisis["coherencia_local"] = coherencia_local

            # Coherencia global acumulada
            sims = []
            for i in range(len(self.vectores_preferencia)-1):
                sim = self._similitud_coseno(
                    self.vectores_preferencia[i]["enteros"],
                    self.vectores_preferencia[i+1]["enteros"]
                )
                if not np.isnan(sim):
                    sims.append(sim)
            analisis["coherencia_global_acumulada"] = float(np.mean(sims)) if sims else 0.0
        else:
            analisis["coherencia_local"] = None
            analisis["coherencia_global_acumulada"] = None

        # 3. Diferencias significativas
        analisis["diferencias_significativas"] = self._encontrar_diferencias_significativas(ganador, perdedor)

        # 4. Análisis por componentes
        analisis["componentes"] = self._analizar_componentes(ganador, perdedor)

        return analisis

    def _calcular_vector_preferencia(self, ganador: Dict, perdedor: Dict) -> Dict:
        """Calcula el vector de preferencia normalizado: ganador - perdedor"""
        vector_pref = {}

        # Integers (8 valores discretos)
        vector_pref["enteros"] = ganador["enteros"] - perdedor["enteros"]

        # Distance weights (5 valores continuos)
        vector_pref["distance_weights"] = ganador["distance_weights"] - perdedor["distance_weights"]

        # Spatial params
        vector_pref["spatial"] = {
            "frequency": ganador["spatial"]["frequency"] - perdedor["spatial"]["frequency"],
            "seed": 1.0 if ganador["spatial"]["seed"] != perdedor["spatial"]["seed"] else 0.0,
            "bias": ganador["spatial"]["bias"] - perdedor["spatial"]["bias"]
        }

        # Base vector (n_total dims)
        vector_pref["base_vector"] = ganador["base_vector"] - perdedor["base_vector"]

        # Amplitude (n_total dims)
        vector_pref["amplitude"] = ganador["amplitude"] - perdedor["amplitude"]

        # Slot offsets (11 slots × n_total dims)
        vector_pref["slot_offsets"] = {}
        for slot in self.slot_names:
            vector_pref["slot_offsets"][slot] = (
                ganador["slot_offsets"][slot] - perdedor["slot_offsets"][slot]
            )

        return vector_pref

    def _calcular_coherencia_local(self, vector_pref_actual: Dict) -> Dict:
        """Calcula similitud coseno entre la decisión actual y la anterior"""
        if len(self.vectores_preferencia) == 0:
            return None

        vector_pref_anterior = self.vectores_preferencia[-1]

        coherencias = {}

        # Integers
        coherencias["enteros"] = self._similitud_coseno(
            vector_pref_actual["enteros"],
            vector_pref_anterior["enteros"]
        )

        # Distance weights
        coherencias["distance_weights"] = self._similitud_coseno(
            vector_pref_actual["distance_weights"],
            vector_pref_anterior["distance_weights"]
        )

        # Amplitude
        coherencias["amplitude"] = self._similitud_coseno(
            vector_pref_actual["amplitude"],
            vector_pref_anterior["amplitude"]
        )

        # Base vector (por componentes)
        if self.vocab:
            coherencias["base_vector"] = {
                "color": self._similitud_coseno(
                    vector_pref_actual["base_vector"][self.color_mask],
                    vector_pref_anterior["base_vector"][self.color_mask]
                ),
                "material": self._similitud_coseno(
                    vector_pref_actual["base_vector"][self.material_mask],
                    vector_pref_anterior["base_vector"][self.material_mask]
                ),
                "categories": self._similitud_coseno(
                    vector_pref_actual["base_vector"][self.categories_mask],
                    vector_pref_anterior["base_vector"][self.categories_mask]
                ),
                "processing": self._similitud_coseno(
                    vector_pref_actual["base_vector"][self.processing_mask],
                    vector_pref_anterior["base_vector"][self.processing_mask]
                )
                # "biome" ELIMINADO
            }

        # Slot offsets (promedio de todos los slots)
        coherencias_slots = []
        for slot in self.slot_names:
            sim = self._similitud_coseno(
                vector_pref_actual["slot_offsets"][slot],
                vector_pref_anterior["slot_offsets"][slot]
            )
            if not np.isnan(sim):
                coherencias_slots.append(sim)
        coherencias["slot_offsets_promedio"] = float(np.mean(coherencias_slots)) if coherencias_slots else 0.0

        return coherencias

    def _similitud_coseno(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Calcula similitud coseno entre dos vectores"""
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)

        if norm_a < 1e-10 or norm_b < 1e-10:
            return 0.0

        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

    def _encontrar_diferencias_significativas(self, ganador: Dict, perdedor: Dict) -> List[Dict]:
        """Encuentra las diferencias más significativas entre ganador y perdedor"""
        diferencias = []

        # Integers (8 valores)
        for i in range(8):
            diff = abs(ganador["enteros"][i] - perdedor["enteros"][i])
            if diff > 0:
                diferencias.append({
                    "feature": f"entero_{i}",
                    "categoria": "enteros",
                    "ganador": int(ganador["enteros"][i]),
                    "perdedor": int(perdedor["enteros"][i]),
                    "diff": float(diff)
                })

        # Distance weights (4 valores - SIN BIOME)
        weight_names = ["Color", "Material", "Categories", "Processing"]
        for i, name in enumerate(weight_names):
            diff = abs(ganador["distance_weights"][i] - perdedor["distance_weights"][i])
            if diff > 0.1:  # Umbral mínimo
                diferencias.append({
                    "feature": f"weight_{name}",
                    "categoria": "distance_weights",
                    "ganador": float(ganador["distance_weights"][i]),
                    "perdedor": float(perdedor["distance_weights"][i]),
                    "diff": float(diff)
                })

        # Spatial frequency
        diff = abs(ganador["spatial"]["frequency"] - perdedor["spatial"]["frequency"])
        if diff > 0.1:
            diferencias.append({
                "feature": "spatial_frequency",
                "categoria": "spatial",
                "ganador": float(ganador["spatial"]["frequency"]),
                "perdedor": float(perdedor["spatial"]["frequency"]),
                "diff": float(diff)
            })

        # Ordenar por diferencia (descendente) y tomar top 10
        diferencias.sort(key=lambda x: x["diff"], reverse=True)
        return diferencias[:10]

    def _analizar_componentes(self, ganador: Dict, perdedor: Dict) -> Dict:
        """Analiza preferencias en componentes específicos (color, material, slots)"""
        componentes = {}

        if not self.vocab:
            return componentes

        # ANÁLISIS DE COLOR (HSVA)
        color_g = ganador["base_vector"][self.color_mask]
        color_p = perdedor["base_vector"][self.color_mask]

        componentes["color"] = {
            "hue_diff": float(color_g[0] - color_p[0]),
            "saturation_diff": float(color_g[1] - color_p[1]),
            "value_diff": float(color_g[2] - color_p[2]),
            "alpha_diff": float(color_g[3] - color_p[3]),
            "ganador": {
                "hue": float(color_g[0]),
                "saturation": float(color_g[1]),
                "value": float(color_g[2]),
                "alpha": float(color_g[3])
            }
        }

        # ANÁLISIS DE MATERIAL
        material_g = ganador["base_vector"][self.material_mask]
        material_p = perdedor["base_vector"][self.material_mask]

        material_idx_g = int(np.argmax(material_g))
        material_idx_p = int(np.argmax(material_p))

        componentes["material"] = {
            "idx_ganador": material_idx_g,
            "idx_perdedor": material_idx_p,
            "cambio": material_idx_g != material_idx_p
        }

        # ANÁLISIS DE SLOT OFFSETS
        slot_importancias = {}
        for slot in self.slot_names:
            offset_diff = np.linalg.norm(
                ganador["slot_offsets"][slot] - perdedor["slot_offsets"][slot]
            )
            slot_importancias[slot] = float(offset_diff)

        componentes["slot_offsets_importancia"] = slot_importancias

        return componentes

    # ========================================================================
    # MÉTODOS AUXILIARES (Diversidad, Stats, CSV)
    # ========================================================================

    def _calcular_diversidad(self, poblacion: List[Dict]) -> Dict[str, float]:
        """Calcula diversidad genética de la población"""
        base_vectors = np.array([g["base_vector"] for g in poblacion])
        amplitudes = np.array([g["amplitude"] for g in poblacion])
        weights = np.array([g["distance_weights"] for g in poblacion])
        enteros = np.array([g["enteros"] for g in poblacion])

        return {
            "base_vector": float(np.mean(np.std(base_vectors, axis=0))),
            "amplitude": float(np.mean(np.std(amplitudes, axis=0))),
            "distance_weights": float(np.mean(np.std(weights, axis=0))),
            "enteros": float(np.mean(np.std(enteros, axis=0)))
        }

    def _calcular_stats_enteros(self, poblacion: List[Dict]) -> Dict[str, List[float]]:
        """Calcula estadísticas de los 8 enteros"""
        enteros = np.array([g["enteros"] for g in poblacion])

        return {
            "means": enteros.mean(axis=0).tolist(),
            "stds": enteros.std(axis=0).tolist(),
            "mins": enteros.min(axis=0).tolist(),
            "maxs": enteros.max(axis=0).tolist()
        }

    def _calcular_stats_weights(self, poblacion: List[Dict]) -> Dict[str, List[float]]:
        """Calcula estadísticas de los distance_weights"""
        weights = np.array([g["distance_weights"] for g in poblacion])

        return {
            "means": weights.mean(axis=0).tolist(),
            "stds": weights.std(axis=0).tolist(),
            "mins": weights.min(axis=0).tolist(),
            "maxs": weights.max(axis=0).tolist()
        }

    def _escribir_csv(self):
        """Escribe todos los registros en el archivo CSV"""
        if not self.generaciones:
            return

        # Obtener claves (excluyendo analisis_decision que es complejo)
        fieldnames = [k for k in self.generaciones[0].keys() if k != "analisis_decision"]

        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.generaciones)


# ============================================================================
# CONTINÚA EN PARTE 2: Métodos de finalización y generación de PDF
# ============================================================================

    """
    iga_logger.py - PARTE 2 de 2
    
    INSTRUCCIONES: Añadir este código AL FINAL de la PARTE 1
    (después de la línea "# CONTINÚA EN PARTE 2")
    
    Este archivo contiene:
    - Método finalizar()
    - Análisis de coherencia global
    - Todos los métodos de generación de PDF (9 páginas)
    """


    # ============================================================================
    # AÑADIR ESTOS MÉTODOS A LA CLASE IGALogger (continuación)
    # ============================================================================

    def _convertir_a_json_serializable(self, obj):
        """
        Convierte recursivamente objetos numpy y otros tipos no serializables a JSON.

        Args:
            obj: Objeto a convertir

        Returns:
            Versión JSON-serializable del objeto
        """
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {key: self._convertir_a_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convertir_a_json_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._convertir_a_json_serializable(item) for item in obj)
        else:
            return obj

    def finalizar(self, genoma_final: Dict, total_tiempo: float):
        """
        Finaliza el logging y genera todos los informes.

        Args:
            genoma_final: Genoma final seleccionado
            total_tiempo: Time total de ejecución (seconds)
        """
        self.metadata["fin"] = datetime.now().isoformat()
        self.metadata["duracion_total_s"] = total_tiempo
        self.metadata["total_generaciones"] = len(self.generaciones)
        self.metadata["generaciones_con_feedback"] = sum(1 for g in self.generaciones if g["es_feedback"])

        # Guardar genoma final COMPLETO
        self.metadata["genoma_final"] = {
            "enteros": genoma_final["enteros"].tolist(),
            "distance_weights": genoma_final["distance_weights"].tolist(),
            "base_vector": genoma_final["base_vector"].tolist(),
            "amplitude": genoma_final["amplitude"].tolist(),
            "spatial": {
                "frequency": float(genoma_final["spatial"]["frequency"]),
                "seed": int(genoma_final["spatial"]["seed"]),
                "bias": genoma_final["spatial"]["bias"].tolist()
            },
            "slot_offsets": {
                slot: offset.tolist()
                for slot, offset in genoma_final["slot_offsets"].items()
            }
        }

        # Calcular análisis de coherencia global
        if len(self.vectores_preferencia) > 1:
            self.metadata["analisis_coherencia"] = self._calcular_coherencia_global()

        # Convertir t0do a JSON-serializable
        datos_serializables = self._convertir_a_json_serializable({
            "metadata": self.metadata,
            "generaciones": self.generaciones
        })

        # Guardar resumen JSON
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(datos_serializables, f, indent=2, ensure_ascii=False)

        # Generar PDF con gráficos
        if MATPLOTLIB_AVAILABLE:
            self._generar_pdf()

        print(f"\n✅ Logs guardados en: {self.carpeta}")
        print(f"   📄 CSV: {self.csv_path}")
        print(f"   📊 JSON: {self.json_path}")
        if MATPLOTLIB_AVAILABLE:
            print(f"   📈 PDF: {self.pdf_path}")


    def _calcular_coherencia_global(self) -> Dict:
        """Calcula métricas globales de coherencia a partir de todas las decisiones"""
        analisis = {}

        # Extraer decisiones con feedback
        decisiones_feedback = [g for g in self.generaciones
                               if g.get("es_feedback") and "analisis_decision" in g]

        if len(decisiones_feedback) < 2:
            return {"error": "Insuficientes decisiones para análisis"}

        # COHERENCIA TEMPORAL
        coherencias_locales = []
        for g in decisiones_feedback:
            coh = g["analisis_decision"].get("coherencia_local")
            if coh:
                coherencias_locales.append(coh)

        if coherencias_locales:
            # Coherencia por categoría
            analisis["coherencia_por_categoria"] = self._promediar_coherencias(coherencias_locales)

            # Coherencia global
            vals_enteros = [c.get("enteros", 0) for c in coherencias_locales if isinstance(c, dict)]
            analisis["coherencia_global"] = float(np.mean(vals_enteros)) if vals_enteros else 0.0

        # CARACTERÍSTICAS DOMINANTES
        analisis["caracteristicas_dominantes"] = self._identificar_caracteristicas_dominantes(decisiones_feedback)

        # EVOLUCIÓN TEMPORAL
        n = len(coherencias_locales)
        if n >= 3:
            tercio = max(1, n // 3)
            vals_inicio = [c.get("enteros", 0) for c in coherencias_locales[:tercio] if isinstance(c, dict)]
            vals_medio = [c.get("enteros", 0) for c in coherencias_locales[tercio:2 * tercio] if isinstance(c, dict)]
            vals_final = [c.get("enteros", 0) for c in coherencias_locales[2 * tercio:] if isinstance(c, dict)]

            analisis["evolucion_coherencia"] = {
                "inicio": float(np.mean(vals_inicio)) if vals_inicio else 0.0,
                "medio": float(np.mean(vals_medio)) if vals_medio else 0.0,
                "final": float(np.mean(vals_final)) if vals_final else 0.0
            }

        return analisis


    def _promediar_coherencias(self, coherencias_locales: List[Dict]) -> Dict:
        """Calcula promedios de coherencias por categoría"""
        promedios = {
            "enteros": [],
            "distance_weights": [],
            "amplitude": [],
            "slot_offsets_promedio": []
        }

        if self.vocab:
            promedios["base_vector"] = {
                "color": [], "material": [], "categories": [], "processing": []  # biome eliminado
            }

        for coh in coherencias_locales:
            if not isinstance(coh, dict):
                continue

            for key in ["enteros", "distance_weights", "amplitude", "slot_offsets_promedio"]:
                if key in coh:
                    promedios[key].append(coh[key])

            if self.vocab and "base_vector" in coh and isinstance(coh["base_vector"], dict):
                for comp in ["color", "material", "categories", "processing"]:  # biome eliminado
                    if comp in coh["base_vector"]:
                        promedios["base_vector"][comp].append(coh["base_vector"][comp])

        # Calcular promedios finales
        resultado = {}
        for key, vals in promedios.items():
            if key == "base_vector" and self.vocab:
                resultado[key] = {
                    comp: float(np.mean(v)) if v else 0.0 for comp, v in vals.items()
                }
            else:
                resultado[key] = float(np.mean(vals)) if vals else 0.0

        return resultado


    def _identificar_caracteristicas_dominantes(self, decisiones_feedback: List[Dict]) -> Dict:
        """Identifica qué características son más consistentemente preferidas"""

        # Acumuladores
        enteros_prefs = [{"alto": 0, "bajo": 0, "total_diff": 0} for _ in range(8)]
        weights_prefs = [{"alto": 0, "bajo": 0, "total_diff": 0} for _ in range(4)]  # SIN BIOME
        weight_names = ["Color", "Material", "Categories", "Processing"]  # SIN BIOME

        color_prefs = {
            attr: {"positivo": 0, "negativo": 0, "suma": 0}
            for attr in ["hue", "saturation", "value", "alpha"]
        }

        slot_importancias = {slot: [] for slot in self.slot_names}

        # Procesar cada decisión
        for decision in decisiones_feedback:
            if "analisis_decision" not in decision:
                continue

            analisis = decision["analisis_decision"]

            # Diferencias significativas
            for diff in analisis.get("diferencias_significativas", []):
                if diff["categoria"] == "enteros":
                    idx = int(diff["feature"].split("_")[1])
                    if diff["ganador"] > diff["perdedor"]:
                        enteros_prefs[idx]["alto"] += 1
                    else:
                        enteros_prefs[idx]["bajo"] += 1
                    enteros_prefs[idx]["total_diff"] += diff["diff"]

                elif diff["categoria"] == "distance_weights":
                    nombre = diff["feature"].split("_")[1]
                    idx = weight_names.index(nombre)
                    if diff["ganador"] > diff["perdedor"]:
                        weights_prefs[idx]["alto"] += 1
                    else:
                        weights_prefs[idx]["bajo"] += 1
                    weights_prefs[idx]["total_diff"] += diff["diff"]

            # Componentes de color
            comps = analisis.get("componentes", {})
            if "color" in comps:
                for attr in ["hue", "saturation", "value", "alpha"]:
                    diff_key = f"{attr}_diff"
                    if diff_key in comps["color"]:
                        diff_val = comps["color"][diff_key]
                        if diff_val > 0:
                            color_prefs[attr]["positivo"] += 1
                        elif diff_val < 0:
                            color_prefs[attr]["negativo"] += 1
                        color_prefs[attr]["suma"] += abs(diff_val)

            # Importancia de slots
            if "slot_offsets_importancia" in comps:
                for slot, importancia in comps["slot_offsets_importancia"].items():
                    slot_importancias[slot].append(importancia)

        # Construir resultados de dominancia
        dominancia = {"enteros": [], "distance_weights": [], "color": {}, "slot_offsets": []}

        # Integers
        for i, pref in enumerate(enteros_prefs):
            total = pref["alto"] + pref["bajo"]
            if total > 0:
                consistencia = max(pref["alto"], pref["bajo"]) / total
                dominancia["enteros"].append({
                    "feature": f"entero_{i}",
                    "preferencia": "alto" if pref["alto"] > pref["bajo"] else "bajo",
                    "consistencia": float(consistencia),
                    "magnitud_promedio": float(pref["total_diff"] / total)
                })

        # Distance weights
        for i, pref in enumerate(weights_prefs):
            total = pref["alto"] + pref["bajo"]
            if total > 0:
                consistencia = max(pref["alto"], pref["bajo"]) / total
                dominancia["distance_weights"].append({
                    "feature": weight_names[i],
                    "preferencia": "alto" if pref["alto"] > pref["bajo"] else "bajo",
                    "consistencia": float(consistencia),
                    "magnitud_promedio": float(pref["total_diff"] / total)
                })

        # Color
        for attr, pref in color_prefs.items():
            total = pref["positivo"] + pref["negativo"]
            if total > 0:
                dominancia["color"][attr] = {
                    "preferencia": "positivo" if pref["positivo"] > pref["negativo"] else "negativo",
                    "consistencia": float(max(pref["positivo"], pref["negativo"]) / total),
                    "magnitud_promedio": float(pref["suma"] / total)
                }

        # Slots (ordenar por importancia)
        slot_ranking = []
        for slot, importancias in slot_importancias.items():
            if importancias:
                slot_ranking.append({
                    "slot": slot,
                    "importancia_promedio": float(np.mean(importancias))
                })
        slot_ranking.sort(key=lambda x: x["importancia_promedio"], reverse=True)
        dominancia["slot_offsets"] = slot_ranking[:5]  # Top 5

        return dominancia


    # ========================================================================
    # GENERACIÓN DE PDF
    # ========================================================================

    def _generar_pdf(self):
        """Genera PDF con todos los gráficos de análisis"""
        with PdfPages(self.pdf_path) as pdf:
            gens = [g["generacion"] for g in self.generaciones]
            feedback_gens = [g["generacion"] for g in self.generaciones if g["es_feedback"]]

            # Páginas 1-5: Gráficos estándar (diversidad, enteros, weights, tiempos, resumen)
            self._generar_pagina_diversidad(pdf, gens, feedback_gens)
            self._generar_pagina_enteros(pdf, gens, feedback_gens)
            self._generar_pagina_weights(pdf, gens, feedback_gens)
            self._generar_pagina_tiempos(pdf)
            self._generar_pagina_resumen(pdf)

            # Páginas 6-9: Análisis de coherencia (si hay datos)
            if len(self.vectores_preferencia) > 1:
                self._generar_pagina_coherencia_general(pdf, feedback_gens)

                if self.vocab and len(self.vectores_preferencia) > 0:
                    self._generar_pagina_color(pdf, feedback_gens)

                self._generar_pagina_dominantes(pdf)

                if self.vocab:
                    self._generar_pagina_slots(pdf)


    def _generar_pagina_diversidad(self, pdf, gens, feedback_gens):
        """Página 1: Evolución de diversidad genética"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Genetic Diversity Evolution', fontsize=16, fontweight='bold')

        # Base vector
        axes[0, 0].plot(gens, [g["diversidad_base_vector"] for g in self.generaciones], 'b-', linewidth=2)
        axes[0, 0].scatter(feedback_gens, [g["diversidad_base_vector"] for g in self.generaciones if g["es_feedback"]],
                           c='red', s=100, zorder=5, label='Feedback')
        axes[0, 0].set_title('Base Vector Diversity')
        axes[0, 0].set_xlabel('Generation')
        axes[0, 0].set_ylabel('Standard Deviation')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # Amplitude
        axes[0, 1].plot(gens, [g["diversidad_amplitude"] for g in self.generaciones], 'g-', linewidth=2)
        axes[0, 1].scatter(feedback_gens, [g["diversidad_amplitude"] for g in self.generaciones if g["es_feedback"]],
                           c='red', s=100, zorder=5, label='Feedback')
        axes[0, 1].set_title('Amplitude Diversity')
        axes[0, 1].set_xlabel('Generation')
        axes[0, 1].set_ylabel('Standard Deviation')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # Distance weights
        axes[1, 0].plot(gens, [g["diversidad_distance_weights"] for g in self.generaciones], 'm-', linewidth=2)
        axes[1, 0].scatter(feedback_gens, [g["diversidad_distance_weights"] for g in self.generaciones if g["es_feedback"]],
                           c='red', s=100, zorder=5, label='Feedback')
        axes[1, 0].set_title('Distance Weights Diversity')
        axes[1, 0].set_xlabel('Generation')
        axes[1, 0].set_ylabel('Standard Deviation')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Integers
        axes[1, 1].plot(gens, [g["diversidad_enteros"] for g in self.generaciones], 'orange', linewidth=2)
        axes[1, 1].scatter(feedback_gens, [g["diversidad_enteros"] for g in self.generaciones if g["es_feedback"]],
                           c='red', s=100, zorder=5, label='Feedback')
        axes[1, 1].set_title('Integer Diversity')
        axes[1, 1].set_xlabel('Generation')
        axes[1, 1].set_ylabel('Standard Deviation')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()


    def _generar_pagina_enteros(self, pdf, gens, feedback_gens):
        """Página 2: Evolución de enteros por PAREJAS con Stacked Area Charts"""

        # Definición de parejas
        ENTERO_GROUPS = [
            (0, 1, "Corners", "Normal Corner", "Inverted Corner"),
            (2, 3, "Terrace/Wall", "Terrace", "Wall"),
            (4, 5, "Enclosure", "Con Enclosure", "Sin Enclosure"),
            (6, 7, "Roof", "2 Waters", "Normal")
        ]

        # Crear figura: 4 parejas + balance bars
        fig = plt.figure(figsize=(14, 14))
        gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.4], hspace=0.3, wspace=0.3)
        fig.suptitle('Proportion Evolution - Integer Pairs',
                     fontsize=16, fontweight='bold')

        # Graficar cada pareja
        for idx, (e1, e2, group_name, label1, label2) in enumerate(ENTERO_GROUPS):
            row = idx // 2
            col = idx % 2
            ax = fig.add_subplot(gs[row, col])

            # Extraer medias de ambos enteros (solo torneos)
            torneos = [g for g in self.generaciones if g["es_feedback"]]
            generaciones_feedback = [g["generacion"] for g in torneos]

            means_e1 = [g[f'entero_{e1}_mean'] for g in torneos]
            means_e2 = [g[f'entero_{e2}_mean'] for g in torneos]

            # Calcular proporciones
            import numpy as np
            means_e1 = np.array(means_e1)
            means_e2 = np.array(means_e2)
            total = means_e1 + means_e2
            total[total == 0] = 1  # Evitar división por cero
            prop_e1 = means_e1 / total
            prop_e2 = means_e2 / total

            # Stacked area
            ax.fill_between(generaciones_feedback, 0, prop_e1,
                           alpha=0.7, color='#3498db', label=label1)
            ax.fill_between(generaciones_feedback, prop_e1, 1,
                           alpha=0.7, color='#e74c3c', label=label2)

            # Línea del 50%
            ax.axhline(0.5, color='black', linestyle='--', linewidth=1, alpha=0.5)

            # Marcar puntos de feedback
            ax.scatter(generaciones_feedback, prop_e1, c='darkblue', s=40,
                      zorder=5, edgecolors='white', linewidths=1.5)

            ax.set_xlabel('Generation', fontsize=10)
            ax.set_ylabel('Proportion', fontsize=10)
            ax.set_title(f'{group_name}', fontsize=12, fontweight='bold')
            ax.set_ylim(0, 1)
            ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
            ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'])
            ax.legend(loc='best', fontsize=9)
            ax.grid(True, alpha=0.2, axis='x')

        # Balance Bars (proporción final de cada pareja)
        ax_balance = fig.add_subplot(gs[2, :])

        bar_width = 0.6
        positions = np.arange(len(ENTERO_GROUPS))

        torneos_final = [g for g in self.generaciones if g["es_feedback"]]

        for idx, (e1, e2, group_name, label1, label2) in enumerate(ENTERO_GROUPS):
            # Usar último torneo
            if torneos_final:
                final_e1 = torneos_final[-1][f'entero_{e1}_mean']
                final_e2 = torneos_final[-1][f'entero_{e2}_mean']
                total = final_e1 + final_e2

                if total > 0:
                    prop_e1 = final_e1 / total
                    prop_e2 = final_e2 / total
                else:
                    prop_e1 = prop_e2 = 0.5
            else:
                prop_e1 = prop_e2 = 0.5

            # Barra apilada horizontal
            ax_balance.barh(idx, prop_e1, bar_width,
                           color='#3498db', alpha=0.8, label=label1 if idx == 0 else "")
            ax_balance.barh(idx, prop_e2, bar_width, left=prop_e1,
                           color='#e74c3c', alpha=0.8, label=label2 if idx == 0 else "")

            # Añadir texto con porcentaje
            if prop_e1 > 0.05:
                ax_balance.text(prop_e1/2, idx, f'{prop_e1*100:.0f}%',
                               ha='center', va='center', fontsize=10,
                               fontweight='bold', color='white')
            if prop_e2 > 0.05:
                ax_balance.text(prop_e1 + prop_e2/2, idx, f'{prop_e2*100:.0f}%',
                               ha='center', va='center', fontsize=10,
                               fontweight='bold', color='white')

        ax_balance.set_yticks(positions)
        ax_balance.set_yticklabels([g[2] for g in ENTERO_GROUPS])
        ax_balance.set_xlabel('Proportion Final', fontsize=11, fontweight='bold')
        ax_balance.set_title('Final Preference Balance', fontsize=12, fontweight='bold')
        ax_balance.set_xlim(0, 1)
        ax_balance.axvline(0.5, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax_balance.legend(loc='upper right', ncol=2, fontsize=9)
        ax_balance.grid(True, alpha=0.2, axis='x')

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

    def _generar_pagina_weights(self, pdf, gens, feedback_gens):
        """Página 3: Evolución de distance weights (SIN BIOME)"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Distance Weights Evolution (Mean ± Std)', fontsize=16, fontweight='bold')

        labels_weights = ['Color', 'Material', 'Categories', 'Processing']

        for i in range(4):
            row, col = i // 2, i % 2
            means = [g[f"weight_{i}_mean"] for g in self.generaciones]
            stds = [g[f"weight_{i}_std"] for g in self.generaciones]

            axes[row, col].plot(gens, means, 'g-', linewidth=2, label='Mean')
            axes[row, col].fill_between(gens,
                                        [m - s for m, s in zip(means, stds)],
                                        [m + s for m, s in zip(means, stds)],
                                        alpha=0.3, color='green', label='±1 std')
            axes[row, col].scatter(feedback_gens,
                                   [g[f"weight_{i}_mean"] for g in self.generaciones if g["es_feedback"]],
                                   c='red', s=100, zorder=5, label='Feedback')
            axes[row, col].set_title(f'Weight {i}: {labels_weights[i]}', fontweight='bold')
            axes[row, col].set_xlabel('Generation')
            axes[row, col].set_ylabel('Weight')
            axes[row, col].legend(fontsize=8)
            axes[row, col].grid(True, alpha=0.3)

        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()

    def _generar_pagina_tiempos(self, pdf):
        """Página 4: Análisis de tiempos de decisión"""
        feedback_data = [g for g in self.generaciones
                         if g["es_feedback"] and g["tiempo_decision_s"] is not None]

        if not feedback_data:
            return

        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        fig.suptitle('User Decision Analysis', fontsize=16, fontweight='bold')

        tiempos = [g["tiempo_decision_s"] for g in feedback_data]
        gens_feedback = [g["generacion"] for g in feedback_data]

        # Evolución temporal
        axes[0].plot(gens_feedback, tiempos, 'ro-', linewidth=2, markersize=8)
        axes[0].set_title('Decision Time per Generation')
        axes[0].set_xlabel('Generation')
        axes[0].set_ylabel('Time (seconds)')
        axes[0].grid(True, alpha=0.3)

        # Histograma
        axes[1].hist(tiempos, bins=10, color='skyblue', edgecolor='black', alpha=0.7)
        axes[1].axvline(np.mean(tiempos), color='red', linestyle='--', linewidth=2,
                        label=f'Mean: {np.mean(tiempos):.1f}s')
        axes[1].set_title('Decision Time Distribution')
        axes[1].set_xlabel('Time (seconds)')
        axes[1].set_ylabel('Frequency')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()


    def _generar_pagina_resumen(self, pdf):
        """Página 5: Resumen estadístico"""
        fig = plt.figure(figsize=(12, 10))
        fig.suptitle('Experiment Summary', fontsize=18, fontweight='bold')

        intervalo = self.metadata['total_generaciones'] // max(1, self.metadata['generaciones_con_feedback'])

        stats_text = f"""
    EXPERIMENT METADATA
    {'=' * 60}
    
    Experiment: {self.metadata['experimento']}
    Start: {self.metadata['inicio']}
    End: {self.metadata['fin']}
    Total Duration: {self.metadata['duracion_total_s']:.2f}s ({self.metadata['duracion_total_s'] / 60:.1f} min)
    
    EVOLUTION STATISTICS
    {'=' * 60}
    
    Total Generations: {self.metadata['total_generaciones']}
    Feedback Generations: {self.metadata['generaciones_con_feedback']}
    Feedback Interval: every {intervalo} generations
    
    FINAL GENOME
    {'=' * 60}
    
    Integers: {self.metadata['genoma_final']['enteros']}
    
    Distance Weights: 
      Color:      {self.metadata['genoma_final']['distance_weights'][0]:.3f}
      Material:   {self.metadata['genoma_final']['distance_weights'][1]:.3f}
      Categories: {self.metadata['genoma_final']['distance_weights'][2]:.3f}
      Processing: {self.metadata['genoma_final']['distance_weights'][3]:.3f}
    
    Spatial Parameters:
      Frequency:  {self.metadata['genoma_final']['spatial']['frequency']:.3f}
      Seed:       {self.metadata['genoma_final']['spatial']['seed']}
    
    Base Vector (first 10 dims): {[f'{x:.3f}' for x in self.metadata['genoma_final']['base_vector'][:10]]}
    Amplitude (first 10 dims):   {[f'{x:.3f}' for x in self.metadata['genoma_final']['amplitude'][:10]]}
    
    FINAL DIVERSITY
    {'=' * 60}
    
    Base Vector: {self.generaciones[-1]['diversidad_base_vector']:.4f}
    Amplitude: {self.generaciones[-1]['diversidad_amplitude']:.4f}
    Distance Weights: {self.generaciones[-1]['diversidad_distance_weights']:.4f}
    Integers: {self.generaciones[-1]['diversidad_enteros']:.4f}
            """

        plt.text(0.1, 0.95, stats_text,
                 transform=fig.transFigure,
                 fontsize=10,
                 verticalalignment='top',
                 fontfamily='monospace',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        plt.axis('off')
        pdf.savefig(fig)
        plt.close()


    def _generar_pagina_coherencia_general(self, pdf, feedback_gens):
        """Página 6: Coherencia de preferencias por categoría"""
        fig = plt.figure(figsize=(12, 10))
        fig.suptitle('Preference Coherence Analysis', fontsize=16, fontweight='bold')

        if "analisis_coherencia" not in self.metadata:
            plt.text(0.5, 0.5, 'Sin datos de coherencia suficientes',
                     ha='center', va='center', fontsize=14)
            plt.axis('off')
            pdf.savefig(fig)
            plt.close()
            return

        coh = self.metadata["analisis_coherencia"]

        # Gráfico de coherencia temporal
        ax1 = plt.subplot(2, 1, 1)

        decisiones_fb = [g for g in self.generaciones if g.get("es_feedback") and "analisis_decision" in g]
        coherencias_enteros = []
        coherencias_weights = []

        for dec in decisiones_fb:
            coh_local = dec["analisis_decision"].get("coherencia_local")
            if coh_local and isinstance(coh_local, dict):
                if "enteros" in coh_local:
                    coherencias_enteros.append(coh_local["enteros"])
                if "distance_weights" in coh_local:
                    coherencias_weights.append(coh_local["distance_weights"])

        if coherencias_enteros:
            gens_con_coherencia = feedback_gens[1:]
            ax1.plot(gens_con_coherencia[:len(coherencias_enteros)], coherencias_enteros,
                     'b-o', linewidth=2, markersize=8, label='Integers')
        if coherencias_weights:
            gens_con_coherencia = feedback_gens[1:]
            ax1.plot(gens_con_coherencia[:len(coherencias_weights)], coherencias_weights,
                     'g-s', linewidth=2, markersize=8, label='Distance Weights')

        ax1.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        ax1.set_title('Temporal Decision Coherence (Cosine Similarity)', fontsize=14)
        ax1.set_xlabel('Generation')
        ax1.set_ylabel('Cosine Similarity')
        ax1.set_ylim(-1.1, 1.1)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Gráfico de barras
        ax2 = plt.subplot(2, 1, 2)

        coh_cat = coh.get("coherencia_por_categoria", {})
        categorias = []
        valores = []

        if "enteros" in coh_cat:
            categorias.append("Integers")
            valores.append(coh_cat["enteros"])
        if "distance_weights" in coh_cat:
            categorias.append("Dist. Weights")
            valores.append(coh_cat["distance_weights"])
        if "amplitude" in coh_cat:
            categorias.append("Amplitude")
            valores.append(coh_cat["amplitude"])
        if "slot_offsets_promedio" in coh_cat:
            categorias.append("Slot Offsets")
            valores.append(coh_cat["slot_offsets_promedio"])

        if self.vocab and "base_vector" in coh_cat and isinstance(coh_cat["base_vector"], dict):
            bv = coh_cat["base_vector"]
            for comp in ["color", "material", "categories", "processing"]:  # biome eliminado
                if comp in bv:
                    categorias.append(f"BV: {comp.title()}")
                    valores.append(bv[comp])

        if categorias and valores:
            colores = ['green' if v > 0.5 else 'orange' if v > 0 else 'red' for v in valores]
            ax2.barh(categorias, valores, color=colores, alpha=0.7, edgecolor='black')
            ax2.axvline(x=0, color='k', linestyle='-', linewidth=1)
            ax2.axvline(x=0.5, color='g', linestyle='--', alpha=0.5, label='High threshold (0.5)')
            ax2.set_xlabel('Average Coherence')
            ax2.set_title('Coherence by Feature Category', fontsize=14)
            ax2.set_xlim(-1, 1)
            ax2.legend()
            ax2.grid(True, alpha=0.3, axis='x')

        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()

    def _generar_pagina_color(self, pdf, feedback_gens):
        """Página 7: Preferencias de color (HSVA) con gradiente visual"""
        decisiones_fb = [g for g in self.generaciones
                         if g.get("es_feedback") and "analisis_decision" in g]

        if not decisiones_fb:
            return

        fig, axes = plt.subplots(4, 1, figsize=(14, 14))  # Más ancho para el gradiente
        fig.suptitle('Color Preference Evolution (HSVA)', fontsize=16, fontweight='bold')

        # Extraer valores de color de los ganadores
        hues, sats, vals, alphas = [], [], [], []
        gens_color = []

        for dec in decisiones_fb:
            comps = dec["analisis_decision"].get("componentes", {})
            if "color" in comps and "ganador" in comps["color"]:
                color = comps["color"]["ganador"]
                hues.append(color.get("hue", 0))
                sats.append(color.get("saturation", 0))
                vals.append(color.get("value", 0))
                alphas.append(color.get("alpha", 1))
                gens_color.append(dec["generacion"])

        if not hues:
            plt.text(0.5, 0.5, 'Sin datos de color suficientes',
                     ha='center', va='center', fontsize=14)
            plt.axis('off')
            pdf.savefig(fig)
            plt.close()
            return

        # ========================================================================
        # GRÁFICO 1: HUE (con gradiente de colores)
        # ========================================================================
        ax_hue = axes[0]

        # Dibujar puntos coloreados según su valor de hue
        for gen, hue in zip(gens_color, hues):
            # Convertir HSV a RGB para colorear el punto
            rgb = plt.matplotlib.colors.hsv_to_rgb([hue, 0.8, 0.8])
            ax_hue.plot(gen, hue, 'o', markersize=10, color=rgb,
                        markeredgecolor='black', markeredgewidth=0.5, zorder=10)

        # Línea conectando puntos (gris suave)
        ax_hue.plot(gens_color, hues, '-', linewidth=1.5, color='gray',
                    alpha=0.5, zorder=5)

        # Mean
        media_hue = np.mean(hues)
        media_rgb = plt.matplotlib.colors.hsv_to_rgb([media_hue, 0.8, 0.8])
        ax_hue.axhline(y=media_hue, color=media_rgb, linestyle='--', linewidth=3,
                       label=f'Mean: {media_hue:.2f}', zorder=8)

        # Configuración del eje
        ax_hue.set_ylabel('Hue (0-1)', fontsize=11)
        ax_hue.set_ylim(0, 1)
        ax_hue.set_xlim(min(gens_color) - 10, max(gens_color) + 10)
        ax_hue.grid(True, alpha=0.3)
        ax_hue.legend(loc='upper right')

        # CREAR BARRA DE GRADIENTE DE COLOR EN EL LADO DERECHO
        # Crear un nuevo eje a la derecha
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        divider = make_axes_locatable(ax_hue)
        cax = divider.append_axes("right", size="2%", pad=0.3)

        # Crear el gradiente HSV
        gradient_hues = np.linspace(0, 1, 256).reshape(-1, 1)
        colors_rgb = []
        for h in np.linspace(0, 1, 256):
            rgb = plt.matplotlib.colors.hsv_to_rgb([h, 0.8, 0.8])
            colors_rgb.append(rgb)

        # Dibujar el gradiente
        cax.imshow(gradient_hues, aspect='auto', cmap=plt.matplotlib.colors.ListedColormap(colors_rgb),
                   origin='lower', extent=[0, 1, 0, 1])
        cax.set_xticks([])
        cax.set_ylabel('')

        # Añadir etiquetas de colores
        cax.set_yticks([0.0, 0.08, 0.17, 0.33, 0.5, 0.67, 0.83, 1.0])
        cax.set_yticklabels(['Red', 'Orange', 'Yellow', 'Green',
                             'Cyan', 'Blue', 'Magenta', 'Red'], fontsize=9)

        # Título descriptivo
        ax_hue.set_title('HUE (Hue) - HSV Color Wheel\n' +
                         '0.0=Red, 0.17=Yellow, 0.33=Green, 0.5=Cyan, 0.67=Blue, 0.83=Magenta',
                         fontsize=11)

        # ========================================================================
        # GRÁFICO 2: SATURATION
        # ========================================================================
        axes[1].plot(gens_color, sats, 'go-', linewidth=2, markersize=8)
        axes[1].set_title('SATURATION (Saturation)\n0=Dull gray, 1=Vivid color', fontsize=11)
        axes[1].set_ylabel('Value (0-1)')
        axes[1].set_ylim(0, 1)
        axes[1].grid(True, alpha=0.3)
        axes[1].axhline(y=np.mean(sats), color='k', linestyle='--',
                        label=f'Mean: {np.mean(sats):.2f}')
        axes[1].legend()

        # ========================================================================
        # GRÁFICO 3: VALUE
        # ========================================================================
        axes[2].plot(gens_color, vals, 'bo-', linewidth=2, markersize=8)
        axes[2].set_title('VALUE (Brightness)\n0=Dark, 1=Bright', fontsize=11)
        axes[2].set_ylabel('Value (0-1)')
        axes[2].set_ylim(0, 1)
        axes[2].grid(True, alpha=0.3)
        axes[2].axhline(y=np.mean(vals), color='k', linestyle='--',
                        label=f'Mean: {np.mean(vals):.2f}')
        axes[2].legend()

        # ========================================================================
        # GRÁFICO 4: ALPHA
        # ========================================================================
        axes[3].plot(gens_color, alphas, 'mo-', linewidth=2, markersize=8)
        axes[3].set_title('ALPHA (Opacity)\n0=Transparent, 1=Opaque', fontsize=11)
        axes[3].set_xlabel('Generation')
        axes[3].set_ylabel('Value (0-1)')
        axes[3].set_ylim(0, 1)
        axes[3].grid(True, alpha=0.3)
        axes[3].axhline(y=np.mean(alphas), color='k', linestyle='--',
                        label=f'Mean: {np.mean(alphas):.2f}')
        axes[3].legend()

        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()


    def _generar_pagina_dominantes(self, pdf):
        """Página 8: Características dominantes"""
        if "analisis_coherencia" not in self.metadata:
            return

        dom = self.metadata["analisis_coherencia"].get("caracteristicas_dominantes", {})

        fig = plt.figure(figsize=(12, 14))
        fig.suptitle('Dominant Decision Features', fontsize=16, fontweight='bold')

        # Integers
        ax1 = plt.subplot(3, 1, 1)
        if "enteros" in dom and dom["enteros"]:
            features = [e["feature"] for e in dom["enteros"][:8]]
            consistencias = [e["consistencia"] for e in dom["enteros"][:8]]
            preferencias = [e["preferencia"] for e in dom["enteros"][:8]]

            colores = ['blue' if p == "alto" else 'orange' for p in preferencias]
            ax1.barh(features, consistencias, color=colores, alpha=0.7, edgecolor='black')
            ax1.set_xlabel('Consistency (0-1)')
            ax1.set_title('Integers: Consistency de Preferencias')
            ax1.set_xlim(0, 1)
            ax1.grid(True, alpha=0.3, axis='x')

            blue_patch = mpatches.Patch(color='blue', label='Prefers HIGH')
            orange_patch = mpatches.Patch(color='orange', label='Prefers LOW')
            ax1.legend(handles=[blue_patch, orange_patch])
        else:
            ax1.text(0.5, 0.5, 'Sin datos de enteros dominantes', ha='center', va='center')
            ax1.axis('off')

        # Distance weights
        ax2 = plt.subplot(3, 1, 2)
        if "distance_weights" in dom and dom["distance_weights"]:
            features = [w["feature"] for w in dom["distance_weights"][:5]]
            consistencias = [w["consistencia"] for w in dom["distance_weights"][:5]]
            preferencias = [w["preferencia"] for w in dom["distance_weights"][:5]]

            colores = ['green' if p == "alto" else 'red' for p in preferencias]
            ax2.barh(features, consistencias, color=colores, alpha=0.7, edgecolor='black')
            ax2.set_xlabel('Consistency (0-1)')
            ax2.set_title('Distance Weights: Consistency de Preferencias')
            ax2.set_xlim(0, 1)
            ax2.grid(True, alpha=0.3, axis='x')

            green_patch = mpatches.Patch(color='green', label='Prefers HIGH')
            red_patch = mpatches.Patch(color='red', label='Prefers LOW')
            ax2.legend(handles=[green_patch, red_patch])
        else:
            ax2.text(0.5, 0.5, 'Sin datos de weights dominantes', ha='center', va='center')
            ax2.axis('off')

        # Color
        ax3 = plt.subplot(3, 1, 3)
        if "color" in dom and dom["color"]:
            attrs = list(dom["color"].keys())
            consistencias = [dom["color"][a]["consistencia"] for a in attrs]
            preferencias = [dom["color"][a]["preferencia"] for a in attrs]

            colores = ['purple' if p == "positivo" else 'brown' for p in preferencias]
            ax3.barh(attrs, consistencias, color=colores, alpha=0.7, edgecolor='black')
            ax3.set_xlabel('Consistency (0-1)')
            ax3.set_title('Color (HSVA): Consistency de Preferencias')
            ax3.set_xlim(0, 1)
            ax3.grid(True, alpha=0.3, axis='x')

            purple_patch = mpatches.Patch(color='purple', label='Prefers POSITIVE (+)')
            brown_patch = mpatches.Patch(color='brown', label='Prefers NEGATIVE (-)')
            ax3.legend(handles=[purple_patch, brown_patch])
        else:
            ax3.text(0.5, 0.5, 'Sin datos de color dominantes', ha='center', va='center')
            ax3.axis('off')

        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()


    def _generar_pagina_slots(self, pdf):
        """Página 9: Análisis de importancia de slots"""
        if "analisis_coherencia" not in self.metadata:
            return

        dom = self.metadata["analisis_coherencia"].get("caracteristicas_dominantes", {})

        fig = plt.figure(figsize=(12, 10))
        fig.suptitle('Slot Offset Importance in Decisions', fontsize=16, fontweight='bold')

        ax = plt.subplot(1, 1, 1)

        if "slot_offsets" in dom and dom["slot_offsets"]:
            slots = [s["slot"] for s in dom["slot_offsets"]]
            importancias = [s["importancia_promedio"] for s in dom["slot_offsets"]]

            colores = plt.cm.viridis(np.linspace(0.3, 0.9, len(slots)))
            bars = ax.barh(slots, importancias, color=colores, alpha=0.8, edgecolor='black')
            ax.set_xlabel('Average Importance (difference norm)')
            ax.set_title('Most Influential Slots in User Decisions')
            ax.grid(True, alpha=0.3, axis='x')

            # Valuees en las barras
            for bar, imp in zip(bars, importancias):
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height() / 2,
                        f'{imp:.3f}', ha='left', va='center', fontsize=9)
        else:
            ax.text(0.5, 0.5, 'Sin datos de slots suficientes',
                    ha='center', va='center', fontsize=14)
            ax.axis('off')

        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()

    # ============================================================================
    # FIN DE LA CLASE IGALogger
    # ============================================================================