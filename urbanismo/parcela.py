from gdpc import Block, Rect
from gdpc.geometry import placeCuboid
from gdpc.geometry import placeRectOutline
from urbanismo.Builder import get_constructor

import city_simulator as city
import statistics




class Parcela:

    def __init__(self):
        self.alto = None
        self.ancho = None
        self.x = None
        self.z = None
        self.uso = None
        self.constructor = None

    def definir(self, alto, ancho, x, y, uso):
        self.alto = alto
        self.ancho = ancho
        self.x = x
        self.z = y
        self.uso = uso

    def desnivel(self) ->int:
        result = 0
        for i in range(self.ancho):
            for j in range(self.alto):
                result += city.inclination_values[self.x+i][self.z + j]
        return result

    def blocks_in_water(self) -> int:
        result = 0
        for i in range(self.ancho):
            for j in range(self.alto):
                if not city.buildable_values[i+self.x][j+self.z]:
                    result+=1
        return result

    def altura_representativa(self) -> int:
        alturas = []
        for i in range(self.ancho):
            for j in range(self.alto):
                alturas.append(city.height_values[self.x + i][self.z + j])

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
        parcela.definir(self.alto, self.ancho, self.x, self.z, self.uso)
        return parcela


    def construir(self):
        get_constructor(self.uso).construir(self)



    def __str__(self):
        return f"Parcela {self.uso} de tamaño {self.alto}x{self.ancho}, ubicada en ({self.x}, {self.z})"

    def level_plot(self):
        altura_parcela = self.altura_representativa()
        for i in range(self.ancho):
            for j in range(self.alto):
                altura_actual = city.height_values[self.x + i][self.z + j]
                bloque = "minecraft:air" if altura_parcela < altura_actual else city.blocks_values[self.x + i][
                    self.z + j]

                y0, y1 = min(altura_parcela, altura_actual), max(altura_parcela, altura_actual)
                if y0==y1: continue
                placeCuboid(
                    city.editor,
                    (city.buildArea.offset.x + self.x + i, y0 + (1 if bloque=="minecraft:air" else 0), city.buildArea.offset.z + self.z + j),
                    (city.buildArea.offset.x + self.x + i, y1, city.buildArea.offset.z + self.z + j),
                    Block(bloque)
                )


