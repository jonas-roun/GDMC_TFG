import random
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set
import matplotlib.pyplot as plt
import numpy as np
from heapq import heappush, heappop

from urbanismo.parcela import Parcela
import city_simulator as city

# -------------------------
# CONSTANTES DEL ALGORITMO ACO (según paper)
# -------------------------
N_HORMIGAS = 30  # Número de hormigas por iteración (paper: 20-50)
N_ITERACIONES = 200  # Número de iteraciones (paper: 100-500)
ALPHA = 1.0  # Importancia de feromonas (paper: α=1)
BETA = 2.0  # Importancia de heurística de distancia (paper: β=2-5)
RHO = 0.1  # Tasa de evaporación global (paper: ρ=0.1)
PHI = 0.1  # Actualización local ACS-style (paper: φ=0.1)
Q = 100.0  # Constante de depósito de feromonas
N_ELITE = 3  # Número de soluciones elite que depositan feromonas
SEED = 42  # Semilla para reproducibilidad (None para aleatorio)

# NUEVAS CONSTANTES PARA DESNIVEL
COSTE_ESCALON = 2.0  # Coste adicional por bloque de desnivel


# -------------------------
# Estructuras básicas
# -------------------------
@dataclass
class Punto:
    x: int
    y: int
    nombre: str = ""
    es_terminal: bool = True

    def assign(self, parcela: Parcela):
        gate_coords = parcela.gate_coord()
        self.x = gate_coords[0]
        self.y = gate_coords[1]
        self.nombre = parcela.uso
        self.es_terminal = True


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, a):
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        else:
            self.parent[rb] = ra
            if self.rank[ra] == self.rank[rb]:
                self.rank[ra] += 1
        return True


# -------------------------
# FUNCIONES AUXILIARES PARA DESNIVEL Y A*
# -------------------------
def obtener_elevacion(x: int, y: int) -> int:
    """Obtiene la elevación del terreno en las coordenadas (x, y)"""
    try:
        return city.height_values[x][y]
    except (IndexError, AttributeError):
        return 0


def calcular_coste_con_desnivel(x1: int, y1: int, x2: int, y2: int) -> float:
    """
    Calcula el coste de moverse entre dos puntos considerando:
    - Distancia Manhattan
    - Desnivel acumulado en el camino

    Para simplicidad, asume que el desnivel se distribuye uniformemente
    en la distancia Manhattan entre los dos puntos.
    """
    dist_manhattan = abs(x2 - x1) + abs(y2 - y1)

    if dist_manhattan == 0:
        return 0.0

    # Obtener elevaciones
    elev1 = obtener_elevacion(x1, y1)
    elev2 = obtener_elevacion(x2, y2)

    # Desnivel total
    desnivel_total = abs(elev2 - elev1)

    # Coste = distancia + (desnivel * factor)
    coste = dist_manhattan + (desnivel_total * COSTE_ESCALON)

    return coste


def a_star_path(start_x: int, start_y: int, end_x: int, end_y: int) -> Tuple[List[Tuple[int, int]], float]:
    """
    Encuentra el camino óptimo entre dos puntos usando A*,
    evitando zonas ocupadas y considerando el desnivel del terreno.

    Returns:
        (camino, coste): Lista de coordenadas (x,y) y coste total del camino
    """
    # Verificar que inicio y fin son válidos
    try:
        if not city.buildable_values[start_x][start_y] or not city.buildable_values[end_x][end_y]:
            return [], float('inf')
    except (IndexError, AttributeError):
        return [], float('inf')

    # Estructuras para A*
    open_set = []
    heappush(open_set, (0, start_x, start_y))

    came_from = {}
    g_score = {(start_x, start_y): 0}

    # Heurística: distancia Manhattan
    def heuristic(x, y):
        return abs(x - end_x) + abs(y - end_y)

    f_score = {(start_x, start_y): heuristic(start_x, start_y)}

    while open_set:
        _, current_x, current_y = heappop(open_set)

        # ¿Llegamos al destino?
        if current_x == end_x and current_y == end_y:
            # Reconstruir camino
            path = []
            x, y = current_x, current_y
            while (x, y) in came_from:
                path.append((x, y))
                x, y = came_from[(x, y)]
            path.append((start_x, start_y))
            path.reverse()

            return path, g_score[(end_x, end_y)]

        # Explorar vecinos (4-conectividad: arriba, abajo, izq, der)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor_x = current_x + dx
            neighbor_y = current_y + dy

            # Verificar límites y disponibilidad
            try:
                if not city.buildable_values[neighbor_x][neighbor_y]:
                    continue
            except (IndexError, AttributeError):
                continue

            # Calcular coste considerando desnivel
            elev_current = obtener_elevacion(current_x, current_y)
            elev_neighbor = obtener_elevacion(neighbor_x, neighbor_y)

            # Coste del movimiento = 1 (distancia) + desnivel
            desnivel = abs(elev_neighbor - elev_current)
            move_cost = 1.0 + (desnivel * COSTE_ESCALON)

            tentative_g = g_score[(current_x, current_y)] + move_cost

            if (neighbor_x, neighbor_y) not in g_score or tentative_g < g_score[(neighbor_x, neighbor_y)]:
                came_from[(neighbor_x, neighbor_y)] = (current_x, current_y)
                g_score[(neighbor_x, neighbor_y)] = tentative_g
                f = tentative_g + heuristic(neighbor_x, neighbor_y)
                f_score[(neighbor_x, neighbor_y)] = f
                heappush(open_set, (f, neighbor_x, neighbor_y))

    # No se encontró camino
    return [], float('inf')


# -------------------------
# ACO para RSTP (FIEL AL PAPER)
# -------------------------
class MinecraftACOSteiner:
    """
    Implementación ACO para Rectilinear Steiner Tree Problem,
    siguiendo FIELMENTE el paper:

    1. Hanan grid construction
    2. Ant constructs MST over terminals using pheromone-guided edge selection
    3. Steiner point insertion to reduce cost
    4. Local pheromone update (ACS-style) during construction
    5. Global pheromone update with elite strategy
    6. Pruning of degree-1 Steiner nodes

    MODIFICACIONES:
    - Coste entre nodos considera desnivel del terreno
    - Conexiones usan A* para evitar zonas ocupadas

    Referencia: "An Ant Colony Optimization Algorithm for the
    Rectilinear Steiner Tree Problem" (paper proporcionado)
    """

    def __init__(self, terminales: List[Punto]):

        if SEED is not None:
            random.seed(SEED)
            np.random.seed(SEED)

        self.terminales = terminales
        self.n_terminales = len(terminales)
        self.n_hormigas = N_HORMIGAS
        self.n_iteraciones = N_ITERACIONES
        self.alpha = ALPHA
        self.beta = BETA
        self.rho = RHO
        self.phi = PHI
        self.Q = Q
        self.n_elite = N_ELITE

        # Cache de caminos A* para exportación (ANTES de construir aristas)
        self.caminos_cache: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}

        # Generar red de Hanan
        self._crear_red_hanan()

        # Construir TODAS las aristas Manhattan entre nodos (con A* y desnivel)
        self._construir_aristas_completas()

        # Inicializar feromonas
        self._inicializar_feromonas()

        # Estado
        self.mejor_solucion = None
        self.mejor_coste = float('inf')
        self.historial_costes = []

    # -------------------------
    # RED DE HANAN
    # -------------------------
    def _crear_red_hanan(self):
        """
        Paper Sección 2: Hanan grid
        Grid formado por líneas verticales y horizontales que pasan
        por cada terminal. Los nodos son las intersecciones.

        MODIFICADO: Excluye puntos donde city.buildable_values[x][y] es False
        """
        xs = sorted(set(p.x for p in self.terminales))
        ys = sorted(set(p.y for p in self.terminales))

        self.coord2idx: Dict[Tuple[int, int], int] = {}
        self.nodos: List[Punto] = []
        idx = 0

        for x in xs:
            for y in ys:
                # Verificar si el punto está en zona ocupada
                try:
                    if not city.buildable_values[x][y]:
                        # Saltar puntos en zona ocupada
                        continue
                except (IndexError, AttributeError):
                    # Si hay error al acceder, incluir el punto por seguridad
                    pass

                es_terminal = any((t.x == x and t.y == y) for t in self.terminales)
                nombre = ""
                if es_terminal:
                    for i, t in enumerate(self.terminales):
                        if t.x == x and t.y == y:
                            nombre = t.nombre or f"T{i}"
                            break
                else:
                    nombre = f"S{idx}"

                p = Punto(x, y, nombre, es_terminal=es_terminal)
                self.coord2idx[(x, y)] = idx
                self.nodos.append(p)
                idx += 1

        # Índices de terminales
        self.terminal_idx = []
        for t in self.terminales:
            if (t.x, t.y) in self.coord2idx:
                self.terminal_idx.append(self.coord2idx[(t.x, t.y)])
            else:
                print(f"WARNING: Terminal {t.nombre} en ({t.x},{t.y}) no está en el grid Hanan")

    def _construir_aristas_completas(self):
        """
        Paper: Las hormigas pueden usar cualquier arista del Hanan grid.

        MODIFICADO: Usa A* para calcular coste real entre nodos,
        considerando zonas ocupadas y desnivel del terreno.
        """
        self.edges: Dict[Tuple[int, int], float] = {}
        n = len(self.nodos)

        print("Calculando aristas con A* y desnivel...")

        # Crear aristas solo entre nodos en misma fila o columna (Manhattan)
        aristas_calculadas = 0
        for i in range(n):
            for j in range(i + 1, n):
                p1 = self.nodos[i]
                p2 = self.nodos[j]

                # Solo conexiones Manhattan (misma x o misma y)
                if p1.x == p2.x or p1.y == p2.y:
                    # Usar A* para encontrar camino real
                    camino, coste = a_star_path(p1.x, p1.y, p2.x, p2.y)

                    if camino and coste < float('inf'):
                        self.edges[(i, j)] = coste
                        self.edges[(j, i)] = coste
                        # Guardar camino para usar después
                        self.caminos_cache[(i, j)] = camino
                        self.caminos_cache[(j, i)] = camino[::-1]
                        aristas_calculadas += 1

        print(f"Aristas calculadas: {aristas_calculadas}")

    def _inicializar_feromonas(self):
        """
        Paper Sección 3.1: Inicialización de feromonas
        τ₀ = 1 / (L_nn * n)
        donde L_nn es longitud de nearest-neighbor heuristic
        """
        # Calcular nearest-neighbor heuristic sobre terminales
        L_nn = self._calcular_nn_heuristic()

        # τ₀ según paper
        self.tau0 = 1.0 / (L_nn * self.n_terminales) if L_nn > 0 else 0.001

        # Inicializar todas las aristas con τ₀
        self.feromonas: Dict[Tuple[int, int], float] = {e: self.tau0 for e in self.edges}

    def _calcular_nn_heuristic(self) -> float:
        """
        Heurística nearest-neighbor: construir árbol greedy eligiendo
        siempre la arista más corta que conecte un nuevo terminal.
        """
        if self.n_terminales <= 1:
            return 1.0

        visitados = {self.terminal_idx[0]}
        coste_total = 0.0

        while len(visitados) < self.n_terminales:
            min_dist = float('inf')
            mejor_arista = None

            for v in visitados:
                for t in self.terminal_idx:
                    if t not in visitados:
                        if (v, t) in self.edges:
                            dist = self.edges[(v, t)]
                            if dist < min_dist:
                                min_dist = dist
                                mejor_arista = (v, t)

            if mejor_arista:
                visitados.add(mejor_arista[1])
                coste_total += min_dist
            else:
                break

        return coste_total if coste_total > 0 else 1.0

    # -------------------------
    # CONSTRUCCIÓN POR HORMIGA (SEGÚN PAPER)
    # -------------------------
    def _construir_por_hormiga(self) -> Tuple[Set[Tuple[int, int]], float]:
        """
        Paper Sección 3.2: Construcción de solución

        PASO 1: Construir MST sobre terminales usando selección probabilística
        PASO 2: Intentar insertar puntos Steiner para reducir coste
        PASO 3: Pruning de hojas Steiner
        """
        # PASO 1: MST sobre terminales
        mst_edges = self._construir_mst_terminales()

        if not mst_edges:
            return set(), float('inf')

        # PASO 2: Expansión con Steiner points
        aristas_expandidas = self._expandir_con_steiner(mst_edges)

        # PASO 3: Pruning
        aristas_final = self._prune_aristas(aristas_expandidas)

        # Calcular coste
        coste = sum(self.edges[(u, v)] for u, v in aristas_final)

        return aristas_final, coste

    def _construir_mst_terminales(self) -> Set[Tuple[int, int]]:
        """
        Paper Sección 3.2.1: Construcción del MST inicial

        Algoritmo tipo Prim modificado:
        - Empezar en terminal aleatorio
        - En cada paso, elegir arista frontera con probabilidad:
          p_ij = [τ_ij^α * η_ij^β] / Σ[τ_ik^α * η_ik^β]
          donde η_ij = 1/d_ij (heurística de distancia)
        - Aplicar actualización local: τ_ij ← (1-φ)τ_ij + φ·τ₀
        """
        uf = UnionFind(len(self.nodos))
        mst_edges: Set[Tuple[int, int]] = set()
        nodos_conectados = {random.choice(self.terminal_idx)}

        # Conectar todos los terminales
        while len(nodos_conectados) < self.n_terminales:
            # Encontrar aristas candidatas (de conectados a no conectados)
            candidatas = []

            for u in nodos_conectados:
                for t_idx in self.terminal_idx:
                    if t_idx in nodos_conectados:
                        continue

                    # Buscar mejor camino Manhattan entre u y t_idx
                    camino, dist = self._mejor_camino_manhattan(u, t_idx)

                    if camino:
                        tau = self._obtener_feromona_camino(camino)
                        eta = 1.0 / (dist + 1e-12)
                        score = (tau ** self.alpha) * (eta ** self.beta)
                        candidatas.append((camino, dist, score, t_idx))

            if not candidatas:
                break

            # Selección probabilística (ruleta)
            scores = np.array([c[2] for c in candidatas])
            suma = scores.sum()

            if suma <= 0:
                elegida = random.choice(candidatas)
            else:
                probs = scores / suma
                idx = np.random.choice(len(candidatas), p=probs)
                elegida = candidatas[idx]

            camino, dist, score, nuevo_terminal = elegida

            # Añadir aristas del camino
            for u, v in camino:
                ar = (min(u, v), max(u, v))
                mst_edges.add(ar)

                # Actualización local de feromonas (Paper Sección 3.2.2)
                self._actualizar_feromona_local((u, v))

            nodos_conectados.add(nuevo_terminal)

        return mst_edges

    def _mejor_camino_manhattan(self, start: int, end: int) -> Tuple[List[Tuple[int, int]], float]:
        """
        Encuentra el mejor camino Manhattan entre dos nodos usando nodos del Hanan grid.
        Usa búsqueda A* simplificada (greedy best-first en grid Manhattan).
        """
        p_start = self.nodos[start]
        p_end = self.nodos[end]

        # Camino directo simple: ir primero en X, luego en Y
        camino = []
        coste_total = 0.0

        # Movimiento en X
        if p_start.x != p_end.x:
            # Buscar nodo intermedio con misma Y que start, misma X que end
            nodo_intermedio = None
            for (x, y), idx in self.coord2idx.items():
                if x == p_end.x and y == p_start.y:
                    nodo_intermedio = idx
                    break

            if nodo_intermedio is not None:
                if (start, nodo_intermedio) in self.edges:
                    camino.append((start, nodo_intermedio))
                    coste_total += self.edges[(start, nodo_intermedio)]
                    start = nodo_intermedio

        # Movimiento en Y
        if (start, end) in self.edges:
            camino.append((start, end))
            coste_total += self.edges[(start, end)]

        return camino, coste_total

    def _obtener_feromona_camino(self, camino: List[Tuple[int, int]]) -> float:
        """Obtiene feromona promedio del camino"""
        if not camino:
            return self.tau0

        suma = 0.0
        for u, v in camino:
            suma += self.feromonas.get((u, v), self.tau0)

        return suma / len(camino)

    def _actualizar_feromona_local(self, arista: Tuple[int, int]):
        """
        Paper Sección 3.2.2: Actualización local
        τ_ij ← (1 - φ)·τ_ij + φ·τ₀
        """
        u, v = arista

        if (u, v) in self.feromonas:
            self.feromonas[(u, v)] = (1 - self.phi) * self.feromonas[(u, v)] + self.phi * self.tau0

        if (v, u) in self.feromonas:
            self.feromonas[(v, u)] = (1 - self.phi) * self.feromonas[(v, u)] + self.phi * self.tau0

    def _expandir_con_steiner(self, mst_edges: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """
        Paper Sección 3.2.3: Expansión con puntos Steiner

        Para cada arista del MST, verificar si insertar un punto Steiner
        del Hanan grid reduce la longitud total.

        Para una arista (u,v), si existe punto s tal que:
        d(u,s) + d(s,v) < d(u,v)
        entonces reemplazar (u,v) por (u,s) y (s,v)
        """
        aristas_mejoradas = set(mst_edges)
        mejora = True

        while mejora:
            mejora = False
            aristas_a_revisar = list(aristas_mejoradas)

            for u, v in aristas_a_revisar:
                if (u, v) not in aristas_mejoradas:
                    continue

                mejor_ahorro = 0
                mejor_steiner = None
                dist_original = self.edges[(u, v)]

                # Probar todos los puntos Steiner posibles
                for s in range(len(self.nodos)):
                    if s == u or s == v:
                        continue

                    # Verificar que s esté en el camino Manhattan entre u y v
                    p_u = self.nodos[u]
                    p_v = self.nodos[v]
                    p_s = self.nodos[s]

                    # s debe estar en el rectángulo definido por u y v
                    if not (min(p_u.x, p_v.x) <= p_s.x <= max(p_u.x, p_v.x) and
                            min(p_u.y, p_v.y) <= p_s.y <= max(p_u.y, p_v.y)):
                        continue

                    # Calcular distancia con Steiner
                    if (u, s) in self.edges and (s, v) in self.edges:
                        dist_con_steiner = self.edges[(u, s)] + self.edges[(s, v)]
                        ahorro = dist_original - dist_con_steiner

                        if ahorro > mejor_ahorro:
                            mejor_ahorro = ahorro
                            mejor_steiner = s

                # Si encontramos mejora, aplicarla
                if mejor_steiner is not None and mejor_ahorro > 0:
                    aristas_mejoradas.discard((u, v))
                    aristas_mejoradas.discard((v, u))
                    aristas_mejoradas.add((min(u, mejor_steiner), max(u, mejor_steiner)))
                    aristas_mejoradas.add((min(mejor_steiner, v), max(mejor_steiner, v)))
                    mejora = True

        return aristas_mejoradas

    def _prune_aristas(self, aristas: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """
        Paper Sección 3.2.4: Pruning
        Eliminar iterativamente nodos Steiner de grado 1 (hojas no-terminales)
        """
        aristas_copia = aristas.copy()

        while True:
            # Calcular grados
            grado = {}
            for u, v in aristas_copia:
                grado[u] = grado.get(u, 0) + 1
                grado[v] = grado.get(v, 0) + 1

            # Buscar hoja Steiner
            hoja_steiner = None
            for nodo, deg in grado.items():
                if deg == 1 and not self.nodos[nodo].es_terminal:
                    hoja_steiner = nodo
                    break

            if hoja_steiner is None:
                break

            # Eliminar arista conectada a la hoja
            for u, v in list(aristas_copia):
                if u == hoja_steiner or v == hoja_steiner:
                    aristas_copia.discard((u, v))
                    break

        return aristas_copia

    # -------------------------
    # ACTUALIZACIÓN GLOBAL DE FEROMONAS
    # -------------------------
    def _actualizar_feromonas_global(self, soluciones: List[Tuple[Set[Tuple[int, int]], float]]):
        """
        Paper Sección 3.3: Actualización global de feromonas

        τ_ij ← (1-ρ)·τ_ij + Σ Δτ_ij^k

        Donde Δτ_ij^k = Q/L_k si arista (i,j) está en solución k

        Elite strategy: solo las mejores n_elite soluciones depositan feromona
        """
        # Evaporación
        for e in self.feromonas:
            self.feromonas[e] *= (1 - self.rho)

        # Filtrar soluciones válidas
        validas = [(aristas, coste) for aristas, coste in soluciones
                   if aristas and coste < float('inf')]

        if not validas:
            return

        # Ordenar por coste (mejores primero)
        validas_ordenadas = sorted(validas, key=lambda x: x[1])

        # Elite strategy: solo las mejores n_elite depositan
        n_depositar = min(self.n_elite, len(validas_ordenadas))

        for rank in range(n_depositar):
            aristas, coste = validas_ordenadas[rank]

            # Δτ = Q/L (Paper ecuación 3)
            delta = self.Q / coste

            # Peso por ranking (las mejores depositan más)
            peso = (n_depositar - rank) / n_depositar

            for u, v in aristas:
                if (u, v) in self.feromonas:
                    self.feromonas[(u, v)] += delta * peso
                if (v, u) in self.feromonas:
                    self.feromonas[(v, u)] += delta * peso

        # Depósito extra para best-so-far (Paper Sección 3.3)
        if self.mejor_solucion and self.mejor_coste < float('inf'):
            delta_best = self.Q / self.mejor_coste

            for u, v in self.mejor_solucion:
                if (u, v) in self.feromonas:
                    self.feromonas[(u, v)] += delta_best
                if (v, u) in self.feromonas:
                    self.feromonas[(v, u)] += delta_best

    # -------------------------
    # OPTIMIZACIÓN
    # -------------------------
    def optimizar(self, verbose: bool = True):
        """
        Paper Sección 3: Algoritmo ACO completo
        """
        if verbose:
            print("=" * 70)
            print(" ACO-RSTP CON DESNIVEL Y A*")
            print("=" * 70)
            print(f"Terminales: {self.n_terminales}")
            print(f"Nodos Hanan grid: {len(self.nodos)}")
            print(f"Hormigas: {N_HORMIGAS} | Iteraciones: {N_ITERACIONES}")
            print(f"Parámetros: α={ALPHA} β={BETA} ρ={RHO} φ={PHI} Q={Q}")
            print(f"Coste escalón: {COSTE_ESCALON}")
            print(f"τ₀ (inicial) = {self.tau0:.6f}")
            print("=" * 70)

        for iteracion in range(self.n_iteraciones):
            soluciones_iter = []

            # Cada hormiga construye una solución
            for _ in range(self.n_hormigas):
                aristas, coste = self._construir_por_hormiga()

                if aristas and coste < float('inf'):
                    soluciones_iter.append((aristas, coste))

                    # Actualizar mejor solución
                    if coste < self.mejor_coste:
                        self.mejor_coste = coste
                        self.mejor_solucion = aristas.copy()

            # Actualización global de feromonas
            if soluciones_iter:
                self._actualizar_feromonas_global(soluciones_iter)

            # Guardar histórico
            self.historial_costes.append(self.mejor_coste if self.mejor_coste < float('inf') else None)

            # Verbose cada 10%
            if verbose and ((iteracion + 1) % max(1, self.n_iteraciones // 10) == 0):
                print(f"Iter {iteracion + 1}/{self.n_iteraciones}  |  Mejor coste: {self.mejor_coste:.2f}")

        if verbose:
            print("\n" + "=" * 70)
            print("OPTIMIZACIÓN COMPLETADA")
            print(f"Mejor coste (con desnivel): {self.mejor_coste:.2f}")
            print("=" * 70 + "\n")

        return self.mejor_solucion

    # -------------------------
    # SALIDA Y VISUALIZACIÓN
    # -------------------------
    def obtener_topologia(self):
        """
        Devuelve lista de pares (Punto, Punto) que deben conectarse
        """
        if not self.mejor_solucion:
            return []

        topologia = []
        for u, v in self.mejor_solucion:
            topologia.append((self.nodos[u], self.nodos[v]))

        return topologia

    def exportar_camino_lineas_rectas(self):
        """
        Exporta todos los bloques que forman el camino (para Minecraft)
        MODIFICADO: Usa los caminos A* reales en lugar de líneas rectas
        """
        if not self.mejor_solucion:
            return []

        bloques = set()

        for u, v in self.mejor_solucion:
            # Obtener camino A* desde la cache
            arista_key = (u, v)

            if arista_key in self.caminos_cache:
                camino = self.caminos_cache[arista_key]
                # Añadir todos los bloques del camino
                for x, y in camino:
                    bloques.add((x, y))
            else:
                # Fallback: si no está en cache, calcular ahora
                p1 = self.nodos[u]
                p2 = self.nodos[v]
                camino, _ = a_star_path(p1.x, p1.y, p2.x, p2.y)
                for x, y in camino:
                    bloques.add((x, y))

        self.imprimir_resumen()
        return list(bloques)

    def imprimir_resumen(self):
        """Imprime resumen de la solución"""
        print("\n" + "=" * 60)
        print("RESUMEN SOLUCIÓN")
        print("=" * 60)

        if not self.mejor_solucion:
            print("No se encontró solución válida.")
            return

        print(f"Coste total (con desnivel): {self.mejor_coste:.2f}")
        print(f"Aristas en árbol: {len(self.mejor_solucion)}")

        nodos_usados = set()
        for u, v in self.mejor_solucion:
            nodos_usados.add(u)
            nodos_usados.add(v)

        steiner_usados = sum(1 for n in nodos_usados if not self.nodos[n].es_terminal)
        print(f"Puntos Steiner usados: {steiner_usados}")

        print("\nTOPOLOGÍA (conexiones):")
        print("-" * 60)
        for p1, p2 in self.obtener_topologia():
            tipo1 = "T" if p1.es_terminal else "S"
            tipo2 = "T" if p2.es_terminal else "S"

            # Obtener coste real (con desnivel)
            u = self.coord2idx.get((p1.x, p1.y))
            v = self.coord2idx.get((p2.x, p2.y))

            if u is not None and v is not None:
                coste = self.edges.get((u, v), 0)
                elev1 = obtener_elevacion(p1.x, p1.y)
                elev2 = obtener_elevacion(p2.x, p2.y)
                desnivel = abs(elev2 - elev1)

                print(f"  [{tipo1}] {p1.nombre:8s} ({p1.x:3d},{p1.y:3d},z={elev1:.1f})  <->  "
                      f"[{tipo2}] {p2.nombre:8s} ({p2.x:3d},{p2.y:3d},z={elev2:.1f})  "
                      f"[coste={coste:.1f}, Δz={desnivel:.1f}]")
            else:
                dist = abs(p1.x - p2.x) + abs(p1.y - p2.y)
                print(f"  [{tipo1}] {p1.nombre:8s} ({p1.x:3d},{p1.y:3d})  <->  "
                      f"[{tipo2}] {p2.nombre:8s} ({p2.x:3d},{p2.y:3d})  [dist={dist:.1f}]")

        print("=" * 60 + "\n")

    def visualizar(self):
        """Visualiza el árbol de Steiner y convergencia"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Gráfico 1: Topología
        ax1.set_title("Árbol de Steiner - Topología Final", fontsize=12, fontweight='bold')
        ax1.set_xlabel("X")
        ax1.set_ylabel("Y")
        ax1.grid(True, alpha=0.3)
        ax1.set_aspect('equal')

        # Dibujar grid Hanan (puntos disponibles)
        xs_grid = [p.x for p in self.nodos]
        ys_grid = [p.y for p in self.nodos]
        ax1.scatter(xs_grid, ys_grid, s=15, color="lightgray", alpha=0.5, label="Hanan grid", zorder=1)

        if self.mejor_solucion:
            # Dibujar aristas de la solución (usando caminos A*)
            for u, v in self.mejor_solucion:
                if (u, v) in self.caminos_cache:
                    camino = self.caminos_cache[(u, v)]
                    xs = [coord[0] for coord in camino]
                    ys = [coord[1] for coord in camino]
                    ax1.plot(xs, ys, 'b-', linewidth=2, alpha=0.7, zorder=2)
                else:
                    # Fallback a línea directa si no hay camino
                    p1 = self.nodos[u]
                    p2 = self.nodos[v]
                    ax1.plot([p1.x, p2.x], [p1.y, p2.y], 'b-', linewidth=2, alpha=0.7, zorder=2)

            # Identificar nodos usados
            nodos_usados = set()
            for u, v in self.mejor_solucion:
                nodos_usados.add(u)
                nodos_usados.add(v)

            # Dibujar Steiner usados
            steiner_usados = [i for i in nodos_usados if not self.nodos[i].es_terminal]
            if steiner_usados:
                xs_st = [self.nodos[i].x for i in steiner_usados]
                ys_st = [self.nodos[i].y for i in steiner_usados]
                ax1.scatter(xs_st, ys_st, s=100, c='orange', marker='s',
                            edgecolors='darkorange', linewidths=2, label="Steiner usado", zorder=3)

        # Dibujar terminales (siempre)
        xs_term = [self.nodos[i].x for i in self.terminal_idx]
        ys_term = [self.nodos[i].y for i in self.terminal_idx]
        ax1.scatter(xs_term, ys_term, s=120, c='red', marker='o',
                    edgecolors='darkred', linewidths=2, label="Terminal", zorder=4)

        ax1.legend(loc='best')

        # Gráfico 2: Convergencia
        ax2.set_title("Convergencia del Algoritmo", fontsize=12, fontweight='bold')
        ax2.set_xlabel("Iteración")
        ax2.set_ylabel("Mejor Coste")
        ax2.grid(True, alpha=0.3)

        costes = [c if c is not None else np.nan for c in self.historial_costes]
        ax2.plot(costes, '-o', linewidth=1.5, markersize=3, color='green')

        plt.tight_layout()
        plt.show()


# -------------------------
# EJEMPLO DE USO
# -------------------------
if __name__ == "__main__":
    from random import randint


    # Mock del módulo city para pruebas
    class MockBuildableValues:
        def __init__(self):
            self.size = 200
            self.data = [[True for _ in range(self.size)] for _ in range(self.size)]
            # Bloquear algunas zonas para testing
            for x in range(30, 50):
                for y in range(40, 60):
                    self.data[x][y] = False
            for x in range(80, 100):
                for y in range(80, 100):
                    self.data[x][y] = False

        def __getitem__(self, x):
            return self.data[x]

        def __len__(self):
            return self.size


    class MockElevationValues:
        def __init__(self):
            self.size = 200
            # Crear terreno con algo de desnivel
            self.data = [[0 for _ in range(self.size)] for _ in range(self.size)]

            # Crear algunas colinas y valles
            for x in range(self.size):
                for y in range(self.size):
                    # Patrón de ondulación
                    self.data[x][y] = int(5 * np.sin(x / 20) + 5 * np.cos(y / 20) + 10)

            # Añadir una montaña
            for x in range(60, 90):
                for y in range(60, 90):
                    dist_centro = np.sqrt((x - 75) ** 2 + (y - 75) ** 2)
                    if dist_centro < 15:
                        self.data[x][y] += int(20 * (1 - dist_centro / 15))

        def __getitem__(self, x):
            return self.data[x]

        def __len__(self):
            return self.size


    # Solo para testing - crear mocks
    if not hasattr(city, 'buildable_values'):
        city.buildable_values = MockBuildableValues()
    if not hasattr(city, 'elevation_values'):
        city.elevation_values = MockElevationValues()

    # Generar terminales de ejemplo
    terminales = []
    for i in range(8):
        x = randint(10, 150)
        y = randint(10, 150)
        terminales.append(Punto(x, y, nombre=f"T{i}"))

    # Crear instancia ACO con parámetros del paper
    aco = MinecraftACOSteiner(terminales=terminales)

    # Optimizar
    mejor = aco.optimizar(verbose=True)

    # Mostrar resultados
    aco.imprimir_resumen()

    # Exportar bloques del camino
    bloques = aco.exportar_camino_lineas_rectas()
    print(f"\nTotal de bloques en el camino: {len(bloques)}")

    # Visualizar
    aco.visualizar()