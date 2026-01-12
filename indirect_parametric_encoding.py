import numpy as np
import random
import math
import sqlite3
from typing import Dict, List, Tuple
from colorsys import rgb_to_hsv

# ==============================
# Configuration
# ==============================

PALETTE_SLOTS = [
    "primary",
    "floor",
    "ceiling",
    "roof",
    "window",
    "stairs",
    "light",
    "fence",
    "gate",
    "door",
]

SLOT_CONSTRAINTS = {
    "floor": """
        NOT material = 'glass' AND (
        type = 'natural'
        OR type = 'chiseled'
        OR type = 'log'
        OR (type = 'colored' AND material = 'stone'))
    """,
    "primary": """
        NOT material = 'glass' AND (
        type = 'natural'
        OR type = 'chiseled'
        OR type = 'log'
        OR (type = 'colored' AND material = 'stone'))
    """,
    "ceiling":  """
        NOT material = 'glass' AND (
        type = 'natural'
        OR type = 'chiseled'
        OR type = 'log'
        OR (type = 'colored' AND material = 'stone'))
    """,
    "roof":  """
        NOT material = 'glass' AND (
        type = 'natural'
        OR type = 'chiseled'
        OR type = 'log'
        OR (type = 'colored' AND material = 'stone'))
    """,
    "window": """
        categories = 'glass'
        OR type = 'pane'
    """,
    "stairs": """
        type = 'stairs'
    """,
    "light": """
        type = 'light'
    """,
    "fence": """
        type = 'fence'
    """,
    "gate": """
        type = 'gate'
    """,
    "door": """
        type = 'door'
    """
}



# ==============================
# Vocabulary Builder (one-hot indices)
# ==============================

class VocabularyBuilder:
    """
    Construye vocabularios dinámicos desde la BD para one-hot encoding.
    Se ejecuta una vez al inicio.
    """

    def __init__(self, db_path='data/blocks.db'):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        # Vocabularios extraídos de la BD
        self.material_vocab = self._build_vocab('material')
        self.categories_vocab = self._build_vocab('categories')
        self.processing_vocab = self._build_vocab('processing')
        # self.biome_vocab ELIMINADO - no se usa

        # Dimensionalidad total
        self.n_color = 4  # h, s, v, a (solo HSV + alpha)
        self.n_material = len(self.material_vocab)
        self.n_categories = len(self.categories_vocab)
        self.n_processing = len(self.processing_vocab)
        # self.biome_vocab ELIMINADO - no se usa

        self.n_total = (
                self.n_color +
                self.n_material +
                self.n_categories +
                self.n_processing #+
                # self.n_biome
        )

        print(f"📊 Vocabulario construido:")
        print(f"   Material: {self.n_material} valores")
        print(f"   Categories: {self.n_categories} valores")
        print(f"   Processing: {self.n_processing} valores")
        # print Biome ELIMINADO
        print(f"   Total dimensiones: {self.n_total}")

    def _build_vocab(self, column: str) -> Dict[str, int]:
        """
        Construye vocabulario (valor → índice) para una columna.
        """
        cursor = self.conn.cursor()
        cursor.execute(f'''
            SELECT DISTINCT {column}
            FROM blocks
            WHERE {column} IS NOT NULL AND {column} != ''
            ORDER BY {column}
        ''')

        values = [row[column] for row in cursor.fetchall()]

        # Crear mapeo valor → índice
        vocab = {value: idx for idx, value in enumerate(values)}

        # Añadir valor especial para NULL/desconocido
        vocab['<UNK>'] = len(vocab)

        return vocab

    def close(self):
        self.conn.close()


# ==============================
# Block Embeddings with One-Hot Encoding
# ==============================

class BlockEmbeddings:
    """
    Convierte bloques Minecraft a vectores one-hot.
    """

    def __init__(self, vocab: VocabularyBuilder, db_path='data/blocks.db'):
        self.vocab = vocab
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._cache = {}

    def extraer_vector(self, block_name: str) -> np.ndarray:
        """
        Extrae vector one-hot de un bloque.

        Estructura (normalizada):
        [
            h, s, v, a,                             # Color HSV (4 dims, [0-1])
            material_one_hot...,                    # Material (n_material dims)
            categories_one_hot...,                  # Categories (n_categories dims)
            processing_one_hot...,                  # Processing (n_processing dims)
            # XXX_biome_REMOVED_XXX_one_hot ELIMINADO
        ]

        Todas las dimensiones están en [0, 1].
        """
        if block_name in self._cache:
            return self._cache[block_name]

        cursor = self.conn.cursor()
        cursor.execute('''
                       SELECT r,
                              g,
                              b,
                              a,
                              material,
                              categories,
                              processing
                       FROM blocks
                       WHERE block = ?
                       ''', (block_name,))

        row = cursor.fetchone()
        if not row:
            # Bloque no encontrado, vector por defecto (t0do <UNK>)
            vector = np.zeros(self.vocab.n_total)
            vector[:4] = 0.5  # Color HSV+alpha neutral
            # Activar <UNK> en cada campo one-hot
            vector[4 + self.vocab.material_vocab['<UNK>']] = 1.0
            offset = 4 + self.vocab.n_material
            vector[offset + self.vocab.categories_vocab['<UNK>']] = 1.0
            offset += self.vocab.n_categories
            vector[offset + self.vocab.processing_vocab['<UNK>']] = 1.0
            offset += self.vocab.n_processing
            # vector[offset + self.vocab.biome_vocab['<UNK>']] = 1.0
            self._cache[block_name] = vector
            return vector

        # ========== Color (solo HSV + Alpha) ==========
        r = float(row['r']) / 255.0 if row['r'] else 0.5
        g = float(row['g']) / 255.0 if row['g'] else 0.5
        b = float(row['b']) / 255.0 if row['b'] else 0.5
        a = float(row['a']) / 255.0 if row['a'] else 1.0

        h, s, v = rgb_to_hsv(r, g, b)

        # Solo HSV + Alpha (4 dims)
        color_vector = np.array([h, s, v, a])

        # ========== One-hot encoding ==========
        vector = np.zeros(self.vocab.n_total)

        # Color (HSV + Alpha)
        vector[:4] = color_vector

        offset = 4

        # Material (one-hot)
        material_val = row['material'] if row['material'] else '<UNK>'
        if material_val in self.vocab.material_vocab:
            idx = self.vocab.material_vocab[material_val]
            vector[offset + idx] = 1.0
        else:
            vector[offset + self.vocab.material_vocab['<UNK>']] = 1.0
        offset += self.vocab.n_material

        # Categories (one-hot)
        categories_val = row['categories'] if row['categories'] else '<UNK>'
        if categories_val in self.vocab.categories_vocab:
            idx = self.vocab.categories_vocab[categories_val]
            vector[offset + idx] = 1.0
        else:
            vector[offset + self.vocab.categories_vocab['<UNK>']] = 1.0
        offset += self.vocab.n_categories

        # Processing (one-hot)
        processing_val = row['processing'] if row['processing'] else '<UNK>'
        if processing_val in self.vocab.processing_vocab:
            idx = self.vocab.processing_vocab[processing_val]
            vector[offset + idx] = 1.0
        else:
            vector[offset + self.vocab.processing_vocab['<UNK>']] = 1.0
        offset += self.vocab.n_processing

        # Biome (one-hot)
        # XXX_biome_REMOVED_XXX handling ELIMINADO

        self._cache[block_name] = vector
        return vector

    def buscar_candidatos(self, slot: str) -> List[str]:
        """
        Retorna lista de bloques válidos para un slot funcional.
        """
        constraint = SLOT_CONSTRAINTS.get(slot, "1=1")

        cursor = self.conn.cursor()
        cursor.execute(f'''
            SELECT block FROM blocks
            WHERE {constraint}
        ''')

        return [row['block'] for row in cursor.fetchall()]

    def close(self):
        self.conn.close()


# ==============================
# Genome creation
# ==============================

def crear_genoma_aleatorio():
    global vocab
    """
    Creates a random genome defining a city-wide style field.

    Args:
        n_attr: Dimensionalidad del espacio de atributos (depende del vocabulario)
    """

    n_attr = vocab.n_total
    # Base style vector (center of the latent space)
    base_vector = np.random.uniform(
        low=0.0,
        high=1.0,
        size=n_attr
    )

    # Per-dimension variation amplitude
    amplitude = np.random.uniform(
        low=0.02,
        high=0.25,
        size=n_attr
    )

    # Spatial / structural parameters
    spatial_params = {
        "frequency": random.uniform(0.1, 1.5),
        "seed": random.randint(0, 10_000),
        "bias": np.random.uniform(
            low=-0.2,
            high=0.2,
            size=n_attr
        )
    }

    # Semantic offsets per functional slot
    slot_offsets = {}
    for slot in PALETTE_SLOTS:
        slot_offsets[slot] = np.random.uniform(
            low=-0.4,
            high=0.4,
            size=n_attr
        )

    # ========== NUEVO: Pesos de distancia evolutivos ==========
    # 5 pesos: [color, material, categories, processing, biome]
    distance_weights = np.random.uniform(
        low=0.5,  # Mínimo: no ignorar completamente
        high=3.0,  # Máximo: puede ser muy importante
        size=4  # SIN BIOME
    )
    # ==========================================================

    genoma = {
        "base_vector": base_vector,
        "amplitude": amplitude,
        "spatial": spatial_params,
        "slot_offsets": slot_offsets,
        "distance_weights": distance_weights,  # NUEVO
    }

    return genoma


# ==============================
# Implicit field function
# ==============================

def generar_vector_objetivo(pos: (int, int), slot: str, genoma: Dict) -> np.ndarray:
    """
    Generates a continuous target vector for a given building index
    and functional slot.
    """

    base = genoma["base_vector"]
    amp = genoma["amplitude"]
    offsets = genoma["slot_offsets"][slot]
    spatial = genoma["spatial"]

    freq = spatial["frequency"]
    bias = spatial["bias"]
    seed = spatial["seed"]

    x, y = pos
    r = math.sqrt(x * x + y * y)

    vector = np.zeros_like(base)

    for i in range(len(base)):
        # Deterministic noise per building and dimension
        random.seed(seed + int(x*31) + int(y*17) + i)
        ruido = random.gauss(0, amp[i])

        # Smooth spatial pattern
        patron = (math.sin(x * freq)+ math.cos(y * freq)+ math.sin(r * freq * 0.5)) * amp[i]

        vector[i] = (
                base[i]
                + ruido
                + patron
                + bias[i]
                + offsets[i]
        )

    # Clip to valid range [0, 1]
    vector = np.clip(vector, 0.0, 1.0)

    return vector


# ==============================
# Weighted distance computation
# ==============================

class WeightedDistance:
    """
    Calcula distancias con pesos EVOLUTIVOS y normalización estadística.

    Enfoque híbrido:
    1. Normalización por varianza (para cada componente)
    2. Pesos evolutivos (aprendidos por el IGA)

    Los pesos FORMAN PARTE DEL GENOMA y evolucionan.
    """

    def __init__(self, vocab: VocabularyBuilder, weights: np.ndarray = None):
        self.vocab = vocab

        # Precalcular máscaras de índices
        self.color_mask = slice(0, vocab.n_color)

        offset = vocab.n_color
        self.material_mask = slice(offset, offset + vocab.n_material)

        offset += vocab.n_material
        self.categories_mask = slice(offset, offset + vocab.n_categories)

        offset += vocab.n_categories
        self.processing_mask = slice(offset, offset + vocab.n_processing)

        offset += vocab.n_processing
        # self.biome_mask ELIMINADO

        # Pesos por componente (5 valores)
        if weights is None:
            # Valores por defecto (uniformes)
            self.weights = np.ones(5)
        else:
            self.weights = weights

        # Índices de pesos
        self.W_COLOR = 0
        self.W_MATERIAL = 1
        self.W_CATEGORIES = 2
        self.W_PROCESSING = 3
        # W_BIOME = 4  # ELIMINADO

    def compute(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Calcula distancia euclidiana ponderada.

        Normalización implícita:
        - One-hot ya está normalizado (valores 0 o 1, norma √2)
        - HSV ya está en [0, 1]

        Los pesos controlan importancia relativa.
        """
        dist_sq = 0.0

        # Color (HSV + Alpha)
        color_diff = vec_a[self.color_mask] - vec_b[self.color_mask]
        dist_sq += self.weights[self.W_COLOR] * np.sum(color_diff ** 2)

        # Material
        material_diff = vec_a[self.material_mask] - vec_b[self.material_mask]
        dist_sq += self.weights[self.W_MATERIAL] * np.sum(material_diff ** 2)

        # Categories
        categories_diff = vec_a[self.categories_mask] - vec_b[self.categories_mask]
        dist_sq += self.weights[self.W_CATEGORIES] * np.sum(categories_diff ** 2)

        # Processing
        processing_diff = vec_a[self.processing_mask] - vec_b[self.processing_mask]
        dist_sq += self.weights[self.W_PROCESSING] * np.sum(processing_diff ** 2)

        # Biome
        # self.biome_mask ELIMINADO
        # dist_sq += self.weights[self.W_BIOME] * np.sum(biome_diff ** 2)

        return np.sqrt(dist_sq)


# ==============================
# Constrained Nearest Neighbor Projection
# ==============================

def proyectar_a_bloque(
        vector_objetivo: np.ndarray,
        slot: str,
        embeddings: BlockEmbeddings,
        distance_calculator: WeightedDistance
) -> str:
    """
    Projects a continuous target vector to the nearest valid Minecraft block.

    Uses WEIGHTED Euclidean distance to balance component contributions.
    Functional constraints (slot) filter candidates BEFORE distance computation.
    """
    candidatos = embeddings.buscar_candidatos(slot)

    if not candidatos:
        return "stone"

    # Calcular distancia PONDERADA a cada candidato
    distancias = []
    for bloque in candidatos:
        vector_bloque = embeddings.extraer_vector(bloque)
        distancia = distance_calculator.compute(vector_objetivo, vector_bloque)
        distancias.append((distancia, bloque))

    # Retornar el más cercano
    distancias.sort()
    return distancias[0][1]


# ==============================
# Complete Pipeline
# ==============================

def generar_paleta_edificio(
        pos: (int, int),
        genoma: Dict
) -> Dict[str, str]:
    global vocab, embeddings
    """
    Genera la paleta completa de materiales para un edificio.

    Usa los pesos de distancia del genoma (evolutivos).
    """
    # Crear calculador de distancias con pesos del genoma
    distance_calculator = WeightedDistance(vocab, weights=genoma["distance_weights"])

    paleta = {}

    for slot in PALETTE_SLOTS:
        # Paso 1: Generar vector en espacio continuo
        vector_objetivo = generar_vector_objetivo(pos, slot, genoma)

        # Paso 2: Proyectar a espacio discreto (con pesos evolutivos)
        bloque = proyectar_a_bloque(vector_objetivo, slot, embeddings, distance_calculator)

        paleta[slot] = bloque

    return paleta


# ==============================
# Operadores genéticos
# ==============================

def crossover_genoma(padre1: Dict, padre2: Dict) -> Tuple[Dict, Dict]:
    """
    Crossover uniforme en el espacio de parámetros.
    INCLUYE los pesos de distancia (evolutivos).
    """
    n_attr = len(padre1["base_vector"])

    hijo1 = {}
    hijo2 = {}

    # Base vector: crossover aritmético
    hijo1["base_vector"] = (padre1["base_vector"] + padre2["base_vector"]) / 2
    hijo2["base_vector"] = (padre2["base_vector"] + padre1["base_vector"]) / 2

    # Amplitude: crossover uniforme por dimensión
    hijo1["amplitude"] = np.where(
        np.random.random(n_attr) < 0.5,
        padre1["amplitude"],
        padre2["amplitude"]
    )
    hijo2["amplitude"] = np.where(
        np.random.random(n_attr) < 0.5,
        padre2["amplitude"],
        padre1["amplitude"]
    )

    # Spatial params: uniforme
    if random.random() < 0.5:
        hijo1["spatial"] = {k: v.copy() if isinstance(v, np.ndarray) else v for k, v in padre1["spatial"].items()}
        hijo2["spatial"] = {k: v.copy() if isinstance(v, np.ndarray) else v for k, v in padre2["spatial"].items()}
    else:
        hijo1["spatial"] = {k: v.copy() if isinstance(v, np.ndarray) else v for k, v in padre2["spatial"].items()}
        hijo2["spatial"] = {k: v.copy() if isinstance(v, np.ndarray) else v for k, v in padre1["spatial"].items()}

    # Slot offsets: uniforme por slot
    hijo1["slot_offsets"] = {}
    hijo2["slot_offsets"] = {}

    for slot in PALETTE_SLOTS:
        if random.random() < 0.5:
            hijo1["slot_offsets"][slot] = padre1["slot_offsets"][slot].copy()
            hijo2["slot_offsets"][slot] = padre2["slot_offsets"][slot].copy()
        else:
            hijo1["slot_offsets"][slot] = padre2["slot_offsets"][slot].copy()
            hijo2["slot_offsets"][slot] = padre1["slot_offsets"][slot].copy()

    # ========== NUEVO: Distance weights (crossover aritmético) ==========
    hijo1["distance_weights"] = (padre1["distance_weights"] + padre2["distance_weights"]) / 2
    hijo2["distance_weights"] = (padre2["distance_weights"] + padre1["distance_weights"]) / 2
    # ====================================================================

    return hijo1, hijo2


def mutar_genoma(genoma: Dict, prob_mutacion: float = 0.2, sigma: float = 0.1):
    """
    Mutación gaussiana en el espacio de parámetros.
    """
    n_attr = len(genoma["base_vector"])

    # Mutar base vector
    if random.random() < prob_mutacion:
        noise = np.random.normal(0, sigma, size=n_attr)
        genoma["base_vector"] = np.clip(genoma["base_vector"] + noise, 0.0, 1.0)

    # Mutar amplitude
    if random.random() < prob_mutacion:
        noise = np.random.normal(0, sigma * 0.5, size=n_attr)
        genoma["amplitude"] = np.clip(genoma["amplitude"] + noise, 0.01, 0.5)

    # Mutar spatial params
    if random.random() < prob_mutacion:
        genoma["spatial"]["frequency"] += random.gauss(0, 0.1)
        genoma["spatial"]["frequency"] = max(0.1, genoma["spatial"]["frequency"])

    if random.random() < prob_mutacion:
        genoma["spatial"]["seed"] = random.randint(0, 10_000)

    if random.random() < prob_mutacion:
        noise = np.random.normal(0, sigma * 0.5, size=n_attr)
        genoma["spatial"]["bias"] = np.clip(genoma["spatial"]["bias"] + noise, -0.5, 0.5)

    # Mutar slot offsets
    for slot in PALETTE_SLOTS:
        if random.random() < prob_mutacion * 0.5:
            noise = np.random.normal(0, sigma, size=n_attr)
            genoma["slot_offsets"][slot] = np.clip(
                genoma["slot_offsets"][slot] + noise,
                -0.5, 0.5
            )

    # ========== NUEVO: Mutar distance weights ==========
    if random.random() < prob_mutacion:
        noise = np.random.normal(0, 0.2, size=4)  # SIN BIOME
        genoma["distance_weights"] = np.clip(
            genoma["distance_weights"] + noise,
            0.1,  # Mínimo: no anular completamente
            5.0  # Máximo: puede ser muy importante
        )
    # ===================================================

    return genoma



vocab: VocabularyBuilder
embeddings: BlockEmbeddings


def setup():
    """Inicializa el vocabulario y embeddings. DEBE llamarse antes de usar el módulo."""
    global vocab, embeddings

    print("\n1. Construyendo vocabulario...")
    vocab = VocabularyBuilder('data/blocks.db')

    print("\n2. Inicializando embeddings...")
    embeddings = BlockEmbeddings(vocab, 'data/blocks.db')

    return vocab, embeddings  # NUEVO: Retornar para uso externo


# ==============================
# Test
# ==============================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST: Indirect Parametric Encoding (One-Hot)")
    print("=" * 60)

    # Construir vocabulario
    print("\n1. Construyendo vocabulario...")
    vocab = VocabularyBuilder('data/blocks.db')

    # Crear embeddings manager
    print("\n2. Inicializando embeddings...")
    embeddings = BlockEmbeddings(vocab, 'data/blocks.db')

    # Generar genoma aleatorio
    print("\n3. Generando genoma aleatorio...")
    genoma = crear_genoma_aleatorio()
    print(f"   Dimensionalidad: {vocab.n_total}")
    print(f"   Base vector (primeras 10 dims): {genoma['base_vector'][:10]}")
    print(f"   Distance weights: {genoma['distance_weights']}")

    print("\n4. Generando paletas para 5 edificios...")
    posiciones = [
        (0.0, 0.0),
        (10.0, 0.0),
        (10.0, 10.0),
        (0.0, 10.0),
        (5.0, 5.0),
    ]

    for i, pos in enumerate(posiciones):
        paleta = generar_paleta_edificio(pos, genoma)
        print(f"\n   Edificio {i} en {pos}:")
        for slot in PALETTE_SLOTS:
            print(f"     {slot:15s} → {paleta[slot]}")

    # Test de distancias
    print("\n5. Test de distancias ponderadas...")
    dist_calc = WeightedDistance(vocab, weights=genoma["distance_weights"])
    oak_vec = embeddings.extraer_vector("oak_planks")
    stone_vec = embeddings.extraer_vector("stone")
    spruce_vec = embeddings.extraer_vector("spruce_planks")

    dist_oak_stone = dist_calc.compute(oak_vec, stone_vec)
    dist_oak_spruce = dist_calc.compute(oak_vec, spruce_vec)

    print(f"   oak_planks ↔ stone (ponderada): {dist_oak_stone:.3f}")
    print(f"   birch_planks ↔ bamboo_planks (ponderada): {dist_oak_spruce:.3f}")

    embeddings.close()
    vocab.close()

    print("\n" + "=" * 60)
    print("✓ Test completado")
    print("=" * 60)