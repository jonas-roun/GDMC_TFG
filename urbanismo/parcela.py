from cmath import inf
from enum import IntEnum

from gdpc import Block
from gdpc.geometry import placeCuboid

import city_simulator as city
import statistics


from urbanismo.materials import getBlock

class Direction(IntEnum):
    SOUTH = 0
    WEST = 1
    NORTH = 2
    EAST = 3

class Parcela:

    def __init__(self):
        self.alto = None
        self.ancho = None
        self.x = None
        self.y = None
        self.altura = None
        self.uso = None
        self.constructor = None
        self.mainBlock = getBlock("wall")
        self.floorBlock = getBlock("floor")
        self.columnBlock = getBlock("column")
        self.fenceBlock = getBlock("fence")
        self.door=getBlock("door")
        self.orientation: Direction = None
        self.doorPosition=None

    def definir(self, alto, ancho, x, y, uso):
        self.alto = alto
        self.ancho = ancho
        self.x = x
        self.y = y
        self.uso = uso
        self.altura = self.altura_representativa()

    def desnivel(self) ->int:
        result = 0
        for i in range(self.ancho):
            for j in range(self.alto):
                result += city.inclination_values[self.x+i][self.y+j]
        return result

    def blocks_in_water(self) -> int:
        result = 0
        for i in range(self.ancho):
            for j in range(self.alto):
                if city.blocks_values[i+self.x][j+self.y]=="water":
                    result+=1
        return result

    def altura_representativa(self) -> int:
        alturas = []
        for i in range(self.ancho):
            for j in range(self.alto):
                alturas.append(city.height_values[self.x + i][self.y + j])

        if not alturas:  # seguridad
            return 0

        # Devolver la mediana
        return int(statistics.median(alturas))

    def copy(self):
        parcela = Parcela()
        parcela.definir(self.alto, self.ancho, self.x, self.y, self.uso)
        return parcela


    def __str__(self):
        return f"Parcela {self.uso} de tamaño {self.alto}x{self.ancho}, ubicada en ({self.x}, {self.y})"


    def construir(self):
        from grammar import grammar_entry_point
        blocks = grammar_entry_point.get_room(self)

        # Colocar los bloques en el mundo
        for coord, block in blocks.items():
            city.buildable_values[coord[0]][coord[2]] = False
            if isinstance(block[0], Block):
                city.editor.placeBlock(
                    (coord[0] + city.buildArea.offset.x, coord[1], coord[2] + city.buildArea.offset.z), block)

        coord = self.gate_coord()
        # city.editor.placeBlock(
        #     (coord[0] + city.buildArea.offset.x, self.altura+3, coord[1] + city.buildArea.offset.z), Block("red_concrete"))

        # Confirmar cambios (importante si usamos buffering=True)
        city.editor.flushBuffer()


    def funcion_adecuacion(self) -> int:
        UNEVEN_PENALTY = 0.5
        WATER_PENALTY = 20
        result = 0
        if self.blocks_in_water() >= self.alto * self.ancho *0.9:
            return 100000000000  # EVITAR PARCELAS COMPLETAMENTE (O CASI) EN EL AGUA!!!!!
        result += self.blocks_in_water() * WATER_PENALTY
        result += self.desnivel() * UNEVEN_PENALTY
        result+=abs(self.alto-self.ancho)/10
        return result-self.alto*self.ancho

    def level_plot(self):
        altura_parcela = self.altura_representativa()
        self.altura = altura_parcela
        for i in range(self.ancho):
            for j in range(self.alto):
                altura_actual = city.height_values[self.x + i][self.y + j]
                bloque = "minecraft:air" if altura_parcela < altura_actual else city.blocks_values[self.x + i][
                    self.y + j]

                y0, y1 = min(altura_parcela, altura_actual), max(altura_parcela, altura_actual)
                if y0==y1: continue
                placeCuboid(
                    city.editor,
                    (city.buildArea.offset.x + self.x + i, y0 + (1 if bloque=="minecraft:air" else 0), city.buildArea.offset.z + self.y + j),
                    (city.buildArea.offset.x + self.x + i, y1, city.buildArea.offset.z + self.y + j),
                    Block(bloque)
                )
        self.place_gate()

    def place_gate(self):
        """
        Coloca la puerta en el borde de la parcela donde el exterior
        tiene la menor diferencia de altura con el nivel de la parcela,
        pero asegurando que la puerta no quede enterrada ni flotando.
        """
        self.altura = self.altura_representativa()

        x0, y0 = self.x, self.y
        ancho, alto = self.ancho, self.alto
        max_x = len(city.heightmap) - 1
        max_y = len(city.heightmap[0]) - 1

        candidates = []

        def valid_diff(exterior_x, exterior_y):
            """Calcula diferencia real con el exterior (solo si es transitable)."""
            if not (0 <= exterior_x <= max_x and 0 <= exterior_y <= max_y):
                return None
            # Saltar agua o zonas no construibles
            if city.blocks_values[exterior_x][exterior_y] == "water":
                return None
            ext_h = city.heightmap[exterior_x][exterior_y]
            diff = abs(ext_h - (self.altura+1))
            # Penaliza si está más de 1 bloque por debajo (es un "borde")
            if ext_h < self.altura - 2 or ext_h > self.altura + 2:
                diff += 5  # penalización para puertas imposibles
            return diff

        # NORTE
        if y0 > 0:
            for i in range(ancho):
                diff = valid_diff(x0 + i, y0 - 1)
                if diff is not None:
                    candidates.append((diff, Direction.NORTH, i))
        # SUR
        if y0 + alto < max_y:
            for i in range(ancho):
                diff = valid_diff(x0 + i, y0 + alto)
                if diff is not None:
                    candidates.append((diff, Direction.SOUTH, i))
        # OESTE
        if x0 > 0:
            for j in range(alto):
                diff = valid_diff(x0 - 1, y0 + j)
                if diff is not None:
                    candidates.append((diff, Direction.WEST, j))
        # ESTE
        if x0 + ancho < max_x:
            for j in range(alto):
                diff = valid_diff(x0 + ancho, y0 + j)
                if diff is not None:
                    candidates.append((diff, Direction.EAST, j))

        if not candidates:
            self.orientation = Direction.NORTH
            self.doorPosition = ancho // 2
            return

        # Elegimos el mejor candidato
        candidates.sort(key=lambda x: x[0])
        _, self.orientation, self.doorPosition = candidates[0]

        # Asegurar rango válido
        if self.orientation in (Direction.NORTH, Direction.SOUTH):
            self.doorPosition = max(1, min(self.doorPosition, ancho - 2))
        else:
            self.doorPosition = max(1, min(self.doorPosition, alto - 2))

    def gate_coord(self):
        # ... tu lógica para calcular self.orientation y self.doorPosition ...
        # al final, calcular coordenadas claras (interior y exterior) y devolverlas.

        # Asumiendo self.orientation y self.doorPosition ya establecidos:
        x0, y0 = self.x, self.y
        ancho, alto = self.ancho, self.alto
        d = self.doorPosition

        if d is None or self.orientation is None:
            return None, None  # no se pudo determinar

        if self.orientation == Direction.NORTH:
            interior = (x0 + d, y0-1)
            exterior = (x0 + d, y0 - 1)
        elif self.orientation == Direction.SOUTH:
            interior = (x0 + d, y0 + alto)
            exterior = (x0 + d, y0 + alto)
        elif self.orientation == Direction.WEST:
            interior = (x0-1, y0 + d)
            exterior = (x0 - 1, y0 + d)
        elif self.orientation == Direction.EAST:
            interior = (x0 + ancho, y0 + d)
            exterior = (x0 + ancho, y0 + d)
        else:
            return None, None


        return exterior




