"""
Sistema de logging completo para el Algoritmo Genético Interactivo.
Genera logs detallados en CSV y PDF con gráficos de evolución.
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
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ Matplotlib no disponible - No se generarán PDFs con gráficos")


class IGALogger:
    """
    Logger completo para el Algoritmo Genético Interactivo.
    Registra toda la evolución y genera informes visuales.
    """
    
    def __init__(self, nombre_experimento: str = "IGA_Experiment"):
        """
        Inicializa el logger y crea la carpeta de salida.
        
        Args:
            nombre_experimento: Nombre base del experimento
        """
        # Crear carpeta con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.carpeta = f"logs/{nombre_experimento}_{timestamp}"
        os.makedirs(self.carpeta, exist_ok=True)
        
        # Archivos de salida
        self.csv_path = os.path.join(self.carpeta, "evolucion.csv")
        self.json_path = os.path.join(self.carpeta, "resumen.json")
        self.pdf_path = os.path.join(self.carpeta, "graficos.pdf")
        
        # Datos recopilados
        self.generaciones = []
        self.metadata = {
            "timestamp": timestamp,
            "experimento": nombre_experimento,
            "inicio": datetime.now().isoformat()
        }
        
        print(f"📊 Logger inicializado: {self.carpeta}")
    
    def registrar_generacion(self, 
                            gen: int,
                            es_feedback: bool,
                            poblacion: List[Dict],
                            ganador: Dict = None,
                            seleccion_usuario: str = None,
                            tiempo_decision: float = None):
        """
        Registra información de una generación.
        
        Args:
            gen: Número de generación
            es_feedback: Si hubo feedback del usuario
            poblacion: Población actual (lista de genomas)
            ganador: Genoma ganador (si aplica)
            seleccion_usuario: "A" o "B" (si aplica)
            tiempo_decision: Tiempo que tardó el usuario en decidir (segundos)
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
            
            # Estadísticas de distance_weights
            **{f"weight_{i}_mean": stats_weights["means"][i] for i in range(5)},
            **{f"weight_{i}_std": stats_weights["stds"][i] for i in range(5)},
            
            # Información de feedback
            "seleccion_usuario": seleccion_usuario if es_feedback else None,
            "tiempo_decision_s": tiempo_decision if es_feedback else None,
        }
        
        # Guardar genoma ganador si existe
        if ganador is not None:
            registro["ganador_enteros"] = ganador["enteros"].tolist()
            registro["ganador_distance_weights"] = ganador["distance_weights"].tolist()
        
        self.generaciones.append(registro)
        
        # Escribir en CSV inmediatamente (para no perder datos)
        self._escribir_csv()
    
    def _calcular_diversidad(self, poblacion: List[Dict]) -> Dict[str, float]:
        """
        Calcula diversidad genética de la población.
        Usa desviación estándar como medida de diversidad.
        """
        n = len(poblacion)
        
        # Diversidad en base_vector (promedio de std de cada dimensión)
        base_vectors = np.array([g["base_vector"] for g in poblacion])
        div_base = np.mean(np.std(base_vectors, axis=0))
        
        # Diversidad en amplitude
        amplitudes = np.array([g["amplitude"] for g in poblacion])
        div_amp = np.mean(np.std(amplitudes, axis=0))
        
        # Diversidad en distance_weights
        weights = np.array([g["distance_weights"] for g in poblacion])
        div_weights = np.mean(np.std(weights, axis=0))
        
        # Diversidad en enteros
        enteros = np.array([g["enteros"] for g in poblacion])
        div_enteros = np.mean(np.std(enteros, axis=0))
        
        return {
            "base_vector": float(div_base),
            "amplitude": float(div_amp),
            "distance_weights": float(div_weights),
            "enteros": float(div_enteros)
        }
    
    def _calcular_stats_enteros(self, poblacion: List[Dict]) -> Dict[str, List[float]]:
        """
        Calcula estadísticas de los 8 enteros.
        """
        enteros = np.array([g["enteros"] for g in poblacion])
        
        return {
            "means": enteros.mean(axis=0).tolist(),
            "stds": enteros.std(axis=0).tolist(),
            "mins": enteros.min(axis=0).tolist(),
            "maxs": enteros.max(axis=0).tolist()
        }
    
    def _calcular_stats_weights(self, poblacion: List[Dict]) -> Dict[str, List[float]]:
        """
        Calcula estadísticas de los distance_weights.
        """
        weights = np.array([g["distance_weights"] for g in poblacion])
        
        return {
            "means": weights.mean(axis=0).tolist(),
            "stds": weights.std(axis=0).tolist(),
            "mins": weights.min(axis=0).tolist(),
            "maxs": weights.max(axis=0).tolist()
        }
    
    def _escribir_csv(self):
        """
        Escribe todos los registros en el archivo CSV.
        """
        if not self.generaciones:
            return
        
        # Obtener todas las claves posibles
        fieldnames = list(self.generaciones[0].keys())
        
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.generaciones)
    
    def finalizar(self, genoma_final: Dict, total_tiempo: float):
        """
        Finaliza el logging y genera todos los informes.
        
        Args:
            genoma_final: Genoma final seleccionado
            total_tiempo: Tiempo total de ejecución (segundos)
        """
        self.metadata["fin"] = datetime.now().isoformat()
        self.metadata["duracion_total_s"] = total_tiempo
        self.metadata["total_generaciones"] = len(self.generaciones)
        self.metadata["generaciones_con_feedback"] = sum(1 for g in self.generaciones if g["es_feedback"])
        
        # Guardar genoma final
        self.metadata["genoma_final"] = {
            "enteros": genoma_final["enteros"].tolist(),
            "distance_weights": genoma_final["distance_weights"].tolist(),
            "base_vector_shape": genoma_final["base_vector"].shape,
        }
        
        # Guardar resumen JSON
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": self.metadata,
                "generaciones": self.generaciones
            }, f, indent=2, ensure_ascii=False)
        
        # Generar PDF con gráficos
        if MATPLOTLIB_AVAILABLE:
            self._generar_pdf()
        
        print(f"\n✅ Logs guardados en: {self.carpeta}")
        print(f"   📄 CSV: {self.csv_path}")
        print(f"   📊 JSON: {self.json_path}")
        if MATPLOTLIB_AVAILABLE:
            print(f"   📈 PDF: {self.pdf_path}")
    
    def _generar_pdf(self):
        """
        Genera PDF con gráficos de evolución.
        """
        with PdfPages(self.pdf_path) as pdf:
            # Preparar datos
            gens = [g["generacion"] for g in self.generaciones]
            feedback_gens = [g["generacion"] for g in self.generaciones if g["es_feedback"]]
            
            # Página 1: Diversidad genética
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle('Evolución de la Diversidad Genética', fontsize=16, fontweight='bold')
            
            # Diversidad de base_vector
            axes[0, 0].plot(gens, [g["diversidad_base_vector"] for g in self.generaciones], 'b-', linewidth=2)
            axes[0, 0].scatter(feedback_gens, [g["diversidad_base_vector"] for g in self.generaciones if g["es_feedback"]], 
                              c='red', s=100, zorder=5, label='Feedback')
            axes[0, 0].set_title('Diversidad Base Vector')
            axes[0, 0].set_xlabel('Generación')
            axes[0, 0].set_ylabel('Desviación estándar')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
            
            # Diversidad de amplitude
            axes[0, 1].plot(gens, [g["diversidad_amplitude"] for g in self.generaciones], 'g-', linewidth=2)
            axes[0, 1].scatter(feedback_gens, [g["diversidad_amplitude"] for g in self.generaciones if g["es_feedback"]], 
                              c='red', s=100, zorder=5, label='Feedback')
            axes[0, 1].set_title('Diversidad Amplitude')
            axes[0, 1].set_xlabel('Generación')
            axes[0, 1].set_ylabel('Desviación estándar')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
            
            # Diversidad de distance_weights
            axes[1, 0].plot(gens, [g["diversidad_distance_weights"] for g in self.generaciones], 'm-', linewidth=2)
            axes[1, 0].scatter(feedback_gens, [g["diversidad_distance_weights"] for g in self.generaciones if g["es_feedback"]], 
                              c='red', s=100, zorder=5, label='Feedback')
            axes[1, 0].set_title('Diversidad Distance Weights')
            axes[1, 0].set_xlabel('Generación')
            axes[1, 0].set_ylabel('Desviación estándar')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
            
            # Diversidad de enteros
            axes[1, 1].plot(gens, [g["diversidad_enteros"] for g in self.generaciones], 'orange', linewidth=2)
            axes[1, 1].scatter(feedback_gens, [g["diversidad_enteros"] for g in self.generaciones if g["es_feedback"]], 
                              c='red', s=100, zorder=5, label='Feedback')
            axes[1, 1].set_title('Diversidad Enteros')
            axes[1, 1].set_xlabel('Generación')
            axes[1, 1].set_ylabel('Desviación estándar')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            pdf.savefig(fig)
            plt.close()
            
            # Página 2: Evolución de los 8 enteros (media)
            fig, axes = plt.subplots(4, 2, figsize=(12, 14))
            fig.suptitle('Evolución de los 8 Enteros (Media ± Std)', fontsize=16, fontweight='bold')
            
            for i in range(8):
                row, col = i // 2, i % 2
                means = [g[f"entero_{i}_mean"] for g in self.generaciones]
                stds = [g[f"entero_{i}_std"] for g in self.generaciones]
                
                axes[row, col].plot(gens, means, 'b-', linewidth=2, label='Media')
                axes[row, col].fill_between(gens, 
                                           [m - s for m, s in zip(means, stds)],
                                           [m + s for m, s in zip(means, stds)],
                                           alpha=0.3, label='±1 std')
                axes[row, col].scatter(feedback_gens, 
                                      [g[f"entero_{i}_mean"] for g in self.generaciones if g["es_feedback"]], 
                                      c='red', s=100, zorder=5, label='Feedback')
                axes[row, col].set_title(f'Entero {i}')
                axes[row, col].set_xlabel('Generación')
                axes[row, col].set_ylabel('Valor')
                axes[row, col].legend(fontsize=8)
                axes[row, col].grid(True, alpha=0.3)
                axes[row, col].axhline(y=0, color='k', linestyle='--', alpha=0.3)
            
            plt.tight_layout()
            pdf.savefig(fig)
            plt.close()
            
            # Página 3: Evolución de distance_weights (media)
            fig, axes = plt.subplots(3, 2, figsize=(12, 12))
            fig.suptitle('Evolución de Distance Weights (Media ± Std)', fontsize=16, fontweight='bold')
            
            labels_weights = ['Color', 'Material', 'Categories', 'Processing', 'Biome']
            
            for i in range(5):
                row, col = i // 2, i % 2
                means = [g[f"weight_{i}_mean"] for g in self.generaciones]
                stds = [g[f"weight_{i}_std"] for g in self.generaciones]
                
                axes[row, col].plot(gens, means, 'g-', linewidth=2, label='Media')
                axes[row, col].fill_between(gens, 
                                           [m - s for m, s in zip(means, stds)],
                                           [m + s for m, s in zip(means, stds)],
                                           alpha=0.3, label='±1 std')
                axes[row, col].scatter(feedback_gens, 
                                      [g[f"weight_{i}_mean"] for g in self.generaciones if g["es_feedback"]], 
                                      c='red', s=100, zorder=5, label='Feedback')
                axes[row, col].set_title(f'Weight {i}: {labels_weights[i]}')
                axes[row, col].set_xlabel('Generación')
                axes[row, col].set_ylabel('Peso')
                axes[row, col].legend(fontsize=8)
                axes[row, col].grid(True, alpha=0.3)
            
            # Eliminar último subplot vacío
            fig.delaxes(axes[2, 1])
            
            plt.tight_layout()
            pdf.savefig(fig)
            plt.close()
            
            # Página 4: Tiempos de decisión del usuario
            feedback_data = [g for g in self.generaciones if g["es_feedback"] and g["tiempo_decision_s"] is not None]
            
            if feedback_data:
                fig, axes = plt.subplots(2, 1, figsize=(12, 8))
                fig.suptitle('Análisis de Decisiones del Usuario', fontsize=16, fontweight='bold')
                
                # Tiempos de decisión
                tiempos = [g["tiempo_decision_s"] for g in feedback_data]
                gens_feedback = [g["generacion"] for g in feedback_data]
                
                axes[0].plot(gens_feedback, tiempos, 'ro-', linewidth=2, markersize=8)
                axes[0].set_title('Tiempo de Decisión por Generación')
                axes[0].set_xlabel('Generación')
                axes[0].set_ylabel('Tiempo (segundos)')
                axes[0].grid(True, alpha=0.3)
                
                # Histograma de tiempos
                axes[1].hist(tiempos, bins=10, color='skyblue', edgecolor='black', alpha=0.7)
                axes[1].axvline(np.mean(tiempos), color='red', linestyle='--', linewidth=2, label=f'Media: {np.mean(tiempos):.1f}s')
                axes[1].set_title('Distribución de Tiempos de Decisión')
                axes[1].set_xlabel('Tiempo (segundos)')
                axes[1].set_ylabel('Frecuencia')
                axes[1].legend()
                axes[1].grid(True, alpha=0.3)
                
                plt.tight_layout()
                pdf.savefig(fig)
                plt.close()
            
            # Página 5: Resumen estadístico
            fig = plt.figure(figsize=(12, 10))
            fig.suptitle('Resumen del Experimento', fontsize=18, fontweight='bold')
            
            # Texto con estadísticas
            stats_text = f"""
METADATA DEL EXPERIMENTO
{'='*60}

Experimento: {self.metadata['experimento']}
Inicio: {self.metadata['inicio']}
Fin: {self.metadata['fin']}
Duración total: {self.metadata['duracion_total_s']:.2f} segundos ({self.metadata['duracion_total_s']/60:.1f} minutos)

ESTADÍSTICAS DE EVOLUCIÓN
{'='*60}

Total de generaciones: {self.metadata['total_generaciones']}
Generaciones con feedback: {self.metadata['generaciones_con_feedback']}
Intervalo de feedback: cada {self.metadata['total_generaciones'] // self.metadata['generaciones_con_feedback']} generaciones

GENOMA FINAL
{'='*60}

Enteros: {self.metadata['genoma_final']['enteros']}

Distance Weights: 
  Color:      {self.metadata['genoma_final']['distance_weights'][0]:.3f}
  Material:   {self.metadata['genoma_final']['distance_weights'][1]:.3f}
  Categories: {self.metadata['genoma_final']['distance_weights'][2]:.3f}
  Processing: {self.metadata['genoma_final']['distance_weights'][3]:.3f}
  Biome:      {self.metadata['genoma_final']['distance_weights'][4]:.3f}

DIVERSIDAD FINAL
{'='*60}

Base Vector: {self.generaciones[-1]['diversidad_base_vector']:.4f}
Amplitude: {self.generaciones[-1]['diversidad_amplitude']:.4f}
Distance Weights: {self.generaciones[-1]['diversidad_distance_weights']:.4f}
Enteros: {self.generaciones[-1]['diversidad_enteros']:.4f}
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
