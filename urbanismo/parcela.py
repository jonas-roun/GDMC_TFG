from gdpc import Block, Rect
from gdpc.geometry import placeCuboid
from gdpc.geometry import placeRectOutline

import city_simulator as city
import statistics

class Parcela:

    def __init__(self):
        self.alto = None
        self.ancho = None
        self.x = None
        self.y = None
        self.uso = None

    def definir(self, alto, ancho, x, y, uso):
        self.alto = alto
        self.ancho = ancho
        self.x = x
        self.y = y
        self.uso = uso

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
        parcela.definir(self.alto, self.ancho, self.x, self.y, self.uso)
        return parcela


    def __str__(self):
        return f"Parcela {self.uso} de tamaño {self.alto}x{self.ancho}, ubicada en ({self.x}, {self.y})"

    def level_plot(self):
        altura_parcela = self.altura_representativa()
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
        placeRectOutline(city.editor, Rect(offset=(city.buildArea.offset.x+self.x, city.buildArea.offset.z+self.y), size=(self.ancho, self.alto)) ,altura_parcela+1,Block("minecraft:oak_fence"))