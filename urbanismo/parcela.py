import random

from gdpc import Block, Rect
from gdpc.geometry import placeCuboid

import city_simulator as city
import statistics

from urbanismo.materials import getBlock


class Parcela:

    def __init__(self):
        self.alto = None
        self.ancho = None
        self.x = None
        self.y = None
        self.altura = None
        self.uso = None
        self.constructor = None
        self.desnivel_esquinas = None
        self.floorplan = None
        self.mainBlock = getBlock("wall")
        self.floorBlock = getBlock("floor")
        self.columnBlock = getBlock("column")

    def definir(self, alto, ancho, x, y, uso, floorplan):
        self.alto = alto
        self.ancho = ancho
        self.x = x
        self.y = y
        self.uso = uso
        self.floorplan = floorplan

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
                if not city.buildable_values[i+self.x][j+self.y]:
                    result+=1
        return result



    def altura_representativa(self) -> int:
        alturas = []
        for i in range(self.ancho):
            for j in range(self.alto):
                alturas.append(city.height_values[self.x + i][self.y + j])

        if not alturas:  # por seguridad
            return 0

        # Recorta un 10% superior e inferior
        alturas.sort()
        n = len(alturas)
        k = int(0.1 * n)
        recortadas = alturas[k:n - k] if n > 2 * k else alturas
        return int(statistics.mean(recortadas))


    def validity(self) -> int:
        return self.blocks_in_water()*2500 + self.desnivel()*50

    def copy(self):
        parcela = Parcela()
        parcela.definir(self.alto, self.ancho, self.x, self.y, self.uso, self.floorplan)
        return parcela


    def __str__(self):
        return f"Parcela {self.uso} de tamaño {self.alto}x{self.ancho}, ubicada en ({self.x}, {self.y})"


    def generate_floorplan(self):
        from.Builder import get_constructor
        get_constructor(self, self.uso).create_floorplan(self)

    def construir(self):
        from .Builder import get_constructor
        get_constructor(self, self.uso).build(self)


    def mutar_floorplan(self):
        # mover puerta (exterior)
        # mover casa dentro de parcela
        # cambiar tamaño casa dentro de parcela
        pass

    def level_plot(self):
        altura_parcela = self.altura_representativa()
        self.altura = altura_parcela
        self.desnivel_esquinas = [0,0,0,0]
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

                if(i==0 and j==0):
                    self.desnivel_esquinas[0] = altura_actual-altura_parcela
                elif (i==0 and j==self.ancho-1):
                    self.desnivel_esquinas[1] = altura_actual-altura_parcela
                elif (i==self.alto-1 and j==0):
                    self.desnivel_esquinas[2] = altura_actual-altura_parcela
                elif (i==self.alto-1 and j==self.ancho-1):
                    self.desnivel_esquinas[3] = altura_actual-altura_parcela