import random, pprint

import numpy as np
from gdpc import Block, Rect
from gdpc.geometry import placeRectOutline

import city_simulator as city
from grammar import room_grammar
from .parcela import Parcela
from .materials import getBlock

class LowDesResBuilder:
    # def construir(self, parcela):
    #     self.floorplan = np.zeros((parcela.alto, parcela.ancho), dtype=int)
    #
    #     self.x0 = city.buildArea.offset.x + parcela.x
    #     self.z0 = city.buildArea.offset.z + parcela.y
    #     #placeRectOutline(city.editor, Rect(offset=(x0, z0),
    #            #                            size=(parcela.ancho, parcela.alto)), parcela.altura + 1,
    #            #          Block("minecraft:oak_fence"))
    #     self.mainBlock = getBlock("wall")
    #     self.floorBlock = getBlock("floor")
    #     self.create_floorplan()
    #     self.build_floorplan(parcela)
    #     #placeCuboidHollow(city.editor, (self.x0, parcela.altura, self.z0), (self.x0+parcela.ancho-1, parcela.altura+4, self.z0+parcela.alto-1), self.mainBlock)
    #     print(f"Construyendo chalet con {self.mainBlock} en {parcela.x}, {parcela.y}")
    @staticmethod
    def build(parcela: Parcela):
        blocks = room_grammar.get_room(parcela)

        # Colocar los bloques en el mundo
        for coord, block in blocks.items():
            if isinstance(block[0], Block):
                city.editor.placeBlock((coord[0]+city.buildArea.offset.x, coord[1],coord[2]+city.buildArea.offset.z), block)

        # Confirmar cambios (importante si usamos buffering=True)
        city.editor.flushBuffer()

    @staticmethod
    def create_floorplan(parcela: Parcela) -> None:
        parcela.floorplan = np.zeros((parcela.alto, parcela.ancho), dtype=int)
        alto_total = parcela.alto
        ancho_total = parcela.ancho

        border_value = 1
        fill_value = 2
        corner_value = 3
        door_value = 4

        if alto_total <= 8 and ancho_total <= 8:
            # Parcela pequeña: ocupar to do
            y0, x0 = 0, 0
            alto, ancho = alto_total, ancho_total
        else:
            # Parcela grande: rectángulo aleatorio mínimo 6x6
            alto = random.randint(6, alto_total)
            ancho = random.randint(6, ancho_total)
            y0 = random.randint(0, alto_total - alto)
            x0 = random.randint(0, ancho_total - ancho)

        # Borde
        parcela.floorplan[y0:y0 + alto, x0] = border_value
        parcela.floorplan[y0:y0 + alto, x0 + ancho - 1] = border_value
        parcela.floorplan[y0, x0:x0 + ancho] = border_value
        parcela.floorplan[y0 + alto - 1, x0:x0 + ancho] = border_value

        parcela.floorplan[y0, x0] = corner_value
        parcela.floorplan[y0 + alto - 1, x0] = corner_value
        parcela.floorplan[y0, x0 + ancho - 1] = corner_value
        parcela.floorplan[y0 + alto - 1, x0+ancho-1] = corner_value

        # Lista de coordenadas prohibidas (fila, columna)
        esquinas = [(y0, x0), (y0+alto-1, x0),(y0, x0+ancho-1),(y0+alto-1, x0+ancho-1)]

        # Encuentra todas las coordenadas con old_value
        indices = np.argwhere(parcela.floorplan == border_value)

        # Filtra las prohibidas
        paredes = [tuple(idx) for idx in indices if tuple(idx) not in esquinas]

        if paredes:
            # Elige una coordenada aleatoria entre las válidas
            y, x = paredes[np.random.choice(len(paredes))]
            parcela.floorplan[y, x] = door_value

        parcela.floorplan[y0 + 1:y0 + alto - 1, x0 + 1:x0 + ancho - 1] = fill_value

    @staticmethod
    def build_floorplan(parcela: Parcela):
        x = parcela.x + city.buildArea.offset.x
        y = parcela.y + city.buildArea.offset.z
        placeRectOutline(city.editor, Rect(offset=(x, y),
                                           size=(parcela.ancho, parcela.alto)), parcela.altura + 1,
                         Block("minecraft:cobblestone_wall"))
        alto = parcela.alto
        ancho = parcela.ancho
        pprint.pprint(parcela.floorplan)
        for i in range(alto):
            for j in range(ancho):
                for k in range(5):

                    if parcela.floorplan[i][j] ==1:
                        city.editor.placeBlock((x+j, parcela.altura+k, y+i), parcela.mainBlock)
                    elif parcela.floorplan[i][j] == 2:
                        if k == 0 or k == 4:
                            city.editor.placeBlock((x + j, parcela.altura + k, y + i), parcela.floorBlock)
                    elif parcela.floorplan[i][j]==3:
                        city.editor.placeBlock((x + j, parcela.altura + k, y + i), parcela.columnBlock)
                    elif parcela.floorplan[i][j]==4:
                        if k == 0 or k==3 or k == 4:
                            city.editor.placeBlock((x + j, parcela.altura + k, y + i), parcela.mainBlock)
                        elif k == 1:
                            city.editor.placeBlock((x + j, parcela.altura + k, y + i), Block("air"))
                            city.editor.placeBlock((x + j, parcela.altura + k, y + i), Block("oak_door"))


