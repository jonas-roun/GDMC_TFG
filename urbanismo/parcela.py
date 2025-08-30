import city_simulator as city


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

    def copy(self):
        parcela = Parcela()
        parcela.definir(self.alto, self.ancho, self.x, self.y, self.uso)
        return parcela


    def __str__(self):
        return f"Parcela {self.uso} de tamaño {self.alto}x{self.ancho}, ubicada en ({self.x}, {self.y})"
