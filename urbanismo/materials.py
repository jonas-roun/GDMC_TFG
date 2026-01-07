import sqlite3
import random
from typing import Dict, List, Optional
from config import BLOCKS_DB_PATH

class GestorPaletas:
    def __init__(self, db_path=None):
        """Inicializa conexión a la base de datos de bloques"""
        if db_path is None:
            db_path = BLOCKS_DB_PATH

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna

    def _ejecutar_query(self, query: str, params: tuple = ()) -> List[str]:
        """
        Ejecuta una query y retorna lista de nombres de bloques.
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        return [row['block'] for row in resultados]

    def _seleccionar_aleatorio(self, bloques: List[str]) -> Optional[str]:
        """Selecciona un bloque aleatorio de la lista, o None si está vacía"""
        return random.choice(bloques) if bloques else None

    # ========================================
    # Queries por slot de paleta
    # ========================================

    def get_bloque_suelo(self) -> str:
        """
        Suelo: categorías natural, chiseled, log
        """
        query = '''
                SELECT block \
                FROM blocks
                WHERE type = 'natural'
                   OR type = 'chiseled'
                   OR type = 'log' \
                '''
        bloques = self._ejecutar_query(query)
        return self._seleccionar_aleatorio(bloques) or "stone"

    def get_bloque_pared_primario(self) -> str:
        """
        Pared (primario): categorías natural, chiseled, log
        """
        query = '''
                SELECT block \
                FROM blocks
                WHERE type = 'natural'
                   OR type = 'chiseled'
                   OR type = 'log' OR (type = 'colored' AND categories = 'stone') \
                '''
        bloques = self._ejecutar_query(query)
        return self._seleccionar_aleatorio(bloques) or "cobblestone"

    def get_bloque_pared_secundario(self) -> str:
        """
        Pared (secundario): categorías natural, chiseled, log
        """
        query = '''
                SELECT block \
                FROM blocks
                WHERE type = 'natural'
                   OR type = 'chiseled'
                   OR type = 'log' OR (type = 'colored' AND categories = 'stone')\
                '''
        bloques = self._ejecutar_query(query)
        return self._seleccionar_aleatorio(bloques) or "oak_planks"

    def get_bloque_techo_ceiling(self) -> str:
        """
        Techo (ceiling): categorías natural, chiseled, log
        """
        query = '''
                SELECT block \
                FROM blocks
                WHERE type = 'natural'
                   OR type = 'chiseled'
                   OR type = 'log' OR (type = 'colored' AND categories = 'stone')\
                '''
        bloques = self._ejecutar_query(query)
        return self._seleccionar_aleatorio(bloques) or "dark_oak_planks"

    def get_bloque_techo_roof(self) -> str:
        """
        Techo (roof): categorías natural, chiseled, log + tipo slab
        """
        query = '''
                SELECT block \
                FROM blocks
                WHERE (type = 'natural'
                    OR type = 'chiseled'
                    OR type = 'log')
                   OR type = 'slab' OR (type = 'colored' AND categories = 'stone')\
                '''
        bloques = self._ejecutar_query(query)
        return self._seleccionar_aleatorio(bloques) or "brick_slab"

    def get_bloque_ventana(self) -> str:
        """
        Ventana: material glass O categoría pane
        """
        query = '''
                SELECT block \
                FROM blocks
                WHERE categories = 'glass'
                   OR type = 'pane' \
                '''
        bloques = self._ejecutar_query(query)
        return self._seleccionar_aleatorio(bloques) or "glass"

    def get_bloque_stair(self) -> str:
        """
        Escaleras: categoría stair
        """
        query = '''
                SELECT block \
                FROM blocks
                WHERE type = 'stairs' \
                '''
        bloques = self._ejecutar_query(query)
        return self._seleccionar_aleatorio(bloques) or "oak_stairs"

    def get_bloque_light(self) -> str:
        """
        Iluminación: categoría light
        """
        query = '''
                SELECT block \
                FROM blocks
                WHERE type = 'light' \
                '''
        bloques = self._ejecutar_query(query)
        # Fallback manual porque todavía no están en la BD
        return self._seleccionar_aleatorio(bloques) or "torch"

    def get_bloque_valla(self) -> str:
        """
        Valla: tipo wall
        """
        query = '''
                SELECT block \
                FROM blocks
                WHERE type = 'fence' \
                '''
        bloques = self._ejecutar_query(query)
        return self._seleccionar_aleatorio(bloques) or "cobblestone_wall"

    def get_bloque_gate(self) -> str:
        """
        Puerta de valla: tipo gate
        """
        query = '''
                SELECT block \
                FROM blocks
                WHERE type = 'gate' \
                '''
        bloques = self._ejecutar_query(query)
        return self._seleccionar_aleatorio(bloques) or "oak_fence_gate"

    def get_bloque_door(self) -> str:
        """
        Puerta: tipo door
        """
        query = '''
                SELECT block \
                FROM blocks
                WHERE type = 'door' \
                '''
        bloques = self._ejecutar_query(query)
        return self._seleccionar_aleatorio(bloques) or "oak_door"

    # ========================================
    # Generación de paleta completa
    # ========================================

    def generar_paleta_aleatoria(self) -> Dict[str, str]:
        """
        Genera una paleta completa con todos los slots necesarios.

        Returns:
            Dict con estructura:
            {
                'suelo': 'stone',
                'pared_primario': 'cobblestone',
                'pared_secundario': 'oak_planks',
                'techo_ceiling': 'dark_oak_planks',
                'techo_roof': 'brick_slab',
                'ventana': 'glass',
                'stair': 'oak_stairs',
                'light': 'torch',
                'valla': 'cobblestone_wall',
                'gate': 'oak_fence_gate',
                'door': 'oak_door'
            }
        """
        paleta = {
            'floor': self.get_bloque_suelo(),
            'primary': self.get_bloque_pared_primario(),
            'accent': self.get_bloque_pared_secundario(),
            'ceiling': self.get_bloque_techo_ceiling(),
            'roof': self.get_bloque_techo_roof(),
            'window': self.get_bloque_ventana(),
            'stair': self.get_bloque_stair(),
            'light': self.get_bloque_light(),
            'fence': self.get_bloque_valla(),
            'gate': self.get_bloque_gate(),
            'door': self.get_bloque_door()
        }

        return paleta

    def cerrar(self):
        """Cierra la conexión a la base de datos"""
        self.conn.close()


# ========================================
# Función de conveniencia
# ========================================

def generar_paleta_aleatoria() -> Dict[str, str]:
    """
    Wrapper simple para generar una paleta sin gestionar la conexión manualmente.

    Uso:
        paleta = generar_paleta_aleatoria()
        print(paleta['suelo'])  # 'stone'
    """
    gestor = GestorPaletas()
    paleta = gestor.generar_paleta_aleatoria()
    gestor.cerrar()
    return paleta


# ========================================
# Ejemplo de uso
# ========================================
#
# if __name__ == '__main__':
#     # Generar 5 paletas aleatorias
#     for i in range(5):
#         print(f"\n{'=' * 50}")
#         print(f"PALETA {i + 1}")
#         print('=' * 50)
#
#         paleta = generar_paleta_aleatoria()
#
#         for slot, bloque in paleta.items():
#             print(f"  {slot:20s} → {bloque}")