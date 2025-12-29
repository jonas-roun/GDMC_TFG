from cmath import inf
from enum import IntEnum

from gdpc import Block, Transform
from gdpc.geometry import placeCuboid
from gdpc.model import Model

import city_simulator as city
import statistics

from urbanismo import materials
from urbanismo.materials import generar_paleta_aleatoria
from urbanismo.models import staircase, first_staircase


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
        self.orientation: Direction = None
        self.doorPosition=None
        self.paleta = None

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
        def get_model_coords(model: Model,x:int,y:int,z:int) -> (tuple, int):
            if self.orientation == Direction.NORTH:
                return (x-model.size.x,y,(z+model.size.z//2+1)), 3
            elif self.orientation == Direction.SOUTH:
                return (x+model.size.x,y,z-model.size.z//2-1) , 1
            elif self.orientation == Direction.EAST:
                return (x - model.size.x // 2 - 1, y, z + model.size.z), 2
            elif self.orientation == Direction.WEST:
                return (x + model.size.x // 2 + 1, y, z - model.size.z), 0
            return -1

        # Colocar los bloques en el mundo
        for coord, block in blocks.items():
            city.buildable_values[coord[0]][coord[2]] = False
            if isinstance(block[0], Block):
                city.editor.placeBlock(
                    (coord[0] + city.buildArea.offset.x, coord[1], coord[2] + city.buildArea.offset.z), block)
            elif block[0]=="flower":
                city.editor.placeBlock(
                    (coord[0] + city.buildArea.offset.x, coord[1], coord[2] + city.buildArea.offset.z), materials.getBlock("flower"))
            elif "stair_spawn" in block[0]:
                stairs = staircase if block[0]=="stair_spawn" else first_staircase
                offset, rotation = get_model_coords(stairs, coord[0], coord[1], coord[2])
                substitutions={
                    "cobblestone":self.paleta["primary"],
                    "oak_planks": self.paleta["floor"],
                    "glowstone": self.paleta["light"],
                    "oak_stairs":self.paleta["stairs"]
                }
                stairs.build(city.editor, transformLike=Transform(
                    (offset[0] + city.buildArea.offset.x, offset[1], offset[2] + city.buildArea.offset.z),
                    rotation=rotation), substitutions=substitutions)

        # coord = self.gate_coord()
        # city.editor.placeBlock(
        #     (coord[0] + city.buildArea.offset.x, self.altura+3, coord[1] + city.buildArea.offset.z), Block("red_concrete"))

        city.editor.flushBuffer()


    def funcion_adecuacion(self) -> int:
        UNEVEN_PENALTY = 1
        WATER_PENALTY = 20
        result = 0
        if self.blocks_in_water() >= self.alto * self.ancho *0.8:
            return 100000000000  # EVITAR PARCELAS COMPLETAMENTE (O CASI) EN EL AGUA!!!!!
        result += self.blocks_in_water() * WATER_PENALTY
        result += self.desnivel() * UNEVEN_PENALTY
        result+=abs(self.alto-self.ancho)
        if self.uso== "hiDesRes" and self.ancho<15 and self.alto < 15:
            return 100000*(15-self.ancho)+10*(15-self.alto)
        return result-self.alto*self.ancho/2

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




