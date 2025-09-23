import random, pprint

import numpy as np
from gdpc import Block, Rect
from gdpc.geometry import placeRectOutline

import city_simulator as city
from .parcela import Parcela
from .materials import getBlock

class LowDesResBuilder:
    def __init__(self, parcela: Parcela):
        self.x0 = 0
        self.z0 = 0
        self.floorplan = None
        self.mainBlock = None
        self.floorBlock = None
        self.most_sloped_corner = parcela.desnivel_esquinas.index(max(parcela.desnivel_esquinas))

    def construir(self, parcela):
        self.floorplan = np.zeros((parcela.alto, parcela.ancho), dtype=int)

        self.x0 = city.buildArea.offset.x + parcela.x
        self.z0 = city.buildArea.offset.z + parcela.y
        #placeRectOutline(city.editor, Rect(offset=(x0, z0),
               #                            size=(parcela.ancho, parcela.alto)), parcela.altura + 1,
               #          Block("minecraft:oak_fence"))
        self.mainBlock = getBlock("wall")
        self.floorBlock = getBlock("floor")
        self.create_floorplan()
        self.build_floorplan(parcela)
        #placeCuboidHollow(city.editor, (self.x0, parcela.altura, self.z0), (self.x0+parcela.ancho-1, parcela.altura+4, self.z0+parcela.alto-1), self.mainBlock)
        print(f"Construyendo chalet con {self.mainBlock} en {parcela.x}, {parcela.y}")

    def create_floorplan(self) -> None:
        alto_total = self.floorplan.shape[0]
        ancho_total = self.floorplan.shape[1]

        border_value = 1
        fill_value = 2

        if alto_total <= 8 and ancho_total <= 8:
            # Parcela pequeña: ocupar todo
            y0, x0 = 0, 0
            alto, ancho = alto_total, ancho_total
        else:
            # Parcela grande: rectángulo aleatorio mínimo 6x6
            alto = random.randint(6, alto_total)
            ancho = random.randint(6, ancho_total)
            y0 = random.randint(0, alto_total - alto)
            x0 = random.randint(0, ancho_total - ancho)

        # Borde
        self.floorplan[y0:y0 + alto, x0] = border_value
        self.floorplan[y0:y0 + alto, x0 + ancho - 1] = border_value
        self.floorplan[y0, x0:x0 + ancho] = border_value
        self.floorplan[y0 + alto - 1, x0:x0 + ancho] = border_value


        self.floorplan[y0 + 1:y0 + alto - 1, x0 + 1:x0 + ancho - 1] = fill_value

    def build_floorplan(self, parcela: Parcela):
        placeRectOutline(city.editor, Rect(offset=(self.x0, self.z0),
                                           size=(parcela.ancho, parcela.alto)), parcela.altura + 1,
                         Block("minecraft:cobblestone_wall"))
        alto = parcela.alto
        ancho = parcela.ancho
        pprint.pprint(self.floorplan)
        for i in range(alto):
            for j in range(ancho):
                for k in range(5):
                    if k==0 or k==4:
                        if self.floorplan[i][j]==2:
                            city.editor.placeBlock((self.x0 + j, parcela.altura + k, self.z0 + i), self.floorBlock)

                    if self.floorplan[i][j] ==1:
                        city.editor.placeBlock((self.x0+j, parcela.altura+k, self.z0+i), self.mainBlock)
