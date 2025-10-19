from functools import partial
from random import choices, randint, uniform
from typing import List, Callable, Tuple

import numpy as np

import city_simulator as city
from urbanismo.parcela import Parcela

GenomaCiudad = List[Parcela]
PoblacionMuestra = List[GenomaCiudad]
FitnessFunc = Callable[[GenomaCiudad],int]
PopulateFunc = Callable[[],PoblacionMuestra]
SelectionFunc = Callable[[PoblacionMuestra, FitnessFunc],Tuple[GenomaCiudad, GenomaCiudad]]
CrossoverFunc = Callable[[Tuple[GenomaCiudad, GenomaCiudad]], Tuple[GenomaCiudad, GenomaCiudad]]
MutationFunc = Callable[[GenomaCiudad], GenomaCiudad]

MAX_TRIES = 100
numero_de_parcelas = 0
TAMANO_MINIMO_PARCELA = 6

def set_numero_de_parcela(i):
    global numero_de_parcelas
    numero_de_parcelas = i

def generar_parcela() -> Parcela:
    result = Parcela()
    #empezamos con el menor tamaño posible para restringir menos al principio
    result.ancho = TAMANO_MINIMO_PARCELA
    result.alto = TAMANO_MINIMO_PARCELA
    #evitamos que la primera generación se salga de rango
    result.x = randint(0, city.width-TAMANO_MINIMO_PARCELA)
    result.y = randint(0, city.height-TAMANO_MINIMO_PARCELA)

    result.uso = "lowDesRes" if randint(0,1) == 0 else "hiDesRes"

    # result.generate_floorplan()
    return result

def generar_genoma(parcelas: int) -> GenomaCiudad:
    genoma = []
    for _ in range(parcelas):
        while True:
            parcela = generar_parcela()
            if es_valida_ciudad(genoma + [parcela]):
                genoma.append(parcela)
                break
    return genoma

def generar_poblacion(tamano: int) -> PoblacionMuestra:
    print(numero_de_parcelas)
    return [generar_genoma(numero_de_parcelas) for _ in range(tamano)]

def funcion_adecuacion(ciudad: GenomaCiudad) -> float:
    penalizaciones = 0

    for parcela in ciudad:
        penalizaciones += parcela.funcion_adecuacion()

    fitness = 1/(1+abs(penalizaciones))
    return fitness


def seleccionar_pareja(generacion: PoblacionMuestra, fitness_func: FitnessFunc) -> PoblacionMuestra:
    return choices(
        population=generacion,
        weights=[fitness_func(genoma) for genoma in generacion],
        k=2
    )

def cruce_un_punto(a: GenomaCiudad, b: GenomaCiudad) -> Tuple[GenomaCiudad, GenomaCiudad]:
    if len(a) != len(b):
        raise ValueError("Las dos ciudades no tienen el mismo número de parcelas")

    length = len(a)
    if(length < 2):
        return a,b

    p = randint(1, length-1)

    result1, result2 = [],[]

    for i in range(length):
        if(i<p):
            result1.append(a[i].copy())
            result2.append(b[i].copy())
        else:
            result1.append(b[i].copy())
            result2.append(a[i].copy())

    return result1, result2



def mutar_ciudad(ciudad: GenomaCiudad) -> GenomaCiudad:
    for i in range(len(ciudad)):
        #mutamos cada parcela aleatoriamente
        if uniform(0, 1.5) > 1/(1 + abs(ciudad[i].funcion_adecuacion())):
            mutar_parcela(ciudad, i)
    return ciudad


#   Aplica una mutación aleatoria a la parcela
def mutar_parcela(ciudad:GenomaCiudad, i:int):
    modification = uniform(0,1)
    if(modification < 0.7):
        mover_parcela(ciudad, i)
    elif(modification <= 1):
        cambiar_tamano_parcela(ciudad, i)
    else:
        print("QUE")


def es_valida_ciudad(ciudad: GenomaCiudad) -> bool:
    # Matriz de ocupación (0 = libre, 1 = ocupado)
    grid = [[0 for _ in range(city.buildArea.size.x)] for _ in range(city.buildArea.size.z)]

    for parcela in ciudad:
        if not (0 <= parcela.x and
                0 <= parcela.y and
                parcela.x + parcela.ancho <= city.buildArea.size.x and
                parcela.y + parcela.alto <= city.buildArea.size.z):
            return False
            # Recorremos los bloques de la parcela
        for dx in range(parcela.ancho):
            for dy in range(parcela.alto):
                x = parcela.x + dx
                y = parcela.y + dy
                # Si ya está ocupado -> solapamiento
                if grid[x][y] == 1:
                    return False
                grid[x][y] = 1

    return True


#=========================
# Mutaciones
#=========================
#   Mueve la parcela hasta 20 bloques en cada direccion aleatoriamente
def mover_parcela(ciudad: GenomaCiudad, i:int):
    for _ in range(MAX_TRIES):
        x_mov, y_mov = randint(-20,20), randint(-20,20)
        if is_in_range_move(ciudad[i], x_mov, y_mov) and validar_ciudad_move(ciudad, i, x_mov, y_mov):
            ciudad[i].x += x_mov
            ciudad[i].y += y_mov
            return
    print("No se ha podido mover la parcela")

#   Comprueba que la parcela no se salga de los límites con la modificación
def is_in_range_move(parcela, x_mov, y_mov) -> bool:
    return (0 <= parcela.x+x_mov and city.buildArea.size.x >= parcela.x+parcela.ancho+x_mov and
            0<=parcela.y+y_mov and city.buildArea.size.z >= parcela.y+parcela.alto+y_mov)

def validar_ciudad_move(ciudad: GenomaCiudad, i,x_mov,y_mov:int) -> bool:
    grid = [[0 for _ in range(city.buildArea.size.x)] for _ in range(city.buildArea.size.z)]

    # Recorremos los bloques de la parcela
    for cont in range(len(ciudad)):
        for dx in range(ciudad[cont].ancho):
            for dy in range(ciudad[cont].alto):
                #si es la parcela que estamos moviendo tenemos en cuenta el movimiento
                x = ciudad[cont].x + dx + (x_mov if cont==i else 0)
                y = ciudad[cont].y + dy + (y_mov if cont==i else 0)
                # Si ya está ocupado -> solapamiento
                if grid[x][y] == 1:
                    return False
                grid[x][y] = 1
    return True


def cambiar_tamano_parcela(ciudad: GenomaCiudad, i:int):
    for _ in range(MAX_TRIES):
        x_mod, y_mod = randint(-10,10), randint(-10,10)
        if is_valid_resize(ciudad[i], x_mod, y_mod) and validar_ciudad_resize(ciudad, i, x_mod, y_mod):
            ciudad[i].ancho += x_mod
            ciudad[i].alto += y_mod
            # if x_mod >= 0 and y_mod >= 0:
            #     ciudad[i].floorplan = np.pad(ciudad[i].floorplan, ((0, y_mod), (0, x_mod)), mode='constant', constant_values=0)
            # else:
            #     ciudad[i].generate_floorplan() #si disminuye una dimension rehacer parcela para evitar cortes
            return
    print("No se ha podido cambiar el tamano")


def is_valid_resize(parcela: Parcela, x_mod, y_mod) -> bool:
    return (parcela.ancho+x_mod > TAMANO_MINIMO_PARCELA and city.buildArea.size.x >= parcela.x + parcela.ancho + x_mod and
            parcela.alto+y_mod > TAMANO_MINIMO_PARCELA  and city.buildArea.size.z >= parcela.y + parcela.alto + y_mod)

def validar_ciudad_resize(ciudad: GenomaCiudad, i,x_mod,y_mod:int) -> bool:
    grid = [[0 for _ in range(city.buildArea.size.x)] for _ in range(city.buildArea.size.z)]

    # Recorremos los bloques de la parcela
    for cont in range(len(ciudad)):

        width = ciudad[cont].ancho + (x_mod if cont==i else 0)
        height = ciudad[cont].alto + (y_mod if cont==i else 0)

        for dx in range(width):
            for dy in range(height):
                x = ciudad[cont].x + dx
                y = ciudad[cont].y + dy

                # Si ya está ocupado -> solapamiento
                if grid[x][y] == 1:
                    return False
                grid[x][y] = 1
    return True


#====================================================
# Función principal de evolución
#====================================================

def simular_evolucion(
        populate_func: PopulateFunc,        #generar primera generación
        fitness_func: FitnessFunc,        #valorar individuos
        fitness_limit: int,                     #adecuacion objetivo (cuando algun individuo la alcance se para
        selection_func: SelectionFunc = seleccionar_pareja,
        crossover_func: CrossoverFunc = cruce_un_punto,
        mutation_func: MutationFunc = mutar_ciudad,
        generation_limit: int = 20
) -> Tuple[PoblacionMuestra, int]:
    population = populate_func()    #primera generacion

    for i in range(generation_limit):
        print(f"Generation {i}")
        population = sorted(population,
                            key=lambda genome: fitness_func(genome),
                            reverse=True)

        #si alcanzamos la adecuacion deseada paramos (creo que aqui se podria implementar elitismo)
        if fitness_func(population[0]) > fitness_limit:
            break

        #cogemos las dos mejores soluciones
        next_generation = population[0:2]

        for j in range(len(population)//2 -1):
            parents = selection_func(population, fitness_func)

            for _ in range(MAX_TRIES):
                hijo_a, hijo_b = crossover_func(parents[0], parents[1])
                if es_valida_ciudad(hijo_a) and es_valida_ciudad(hijo_b):
                    break
            else:
                # Si tras MAX_TRIES no consigue hijos válidos, se quedan iguales que los padres
                hijo_a, hijo_b = parents[0], parents[1]

            hijo_a = mutation_func(hijo_a)
            hijo_b = mutation_func(hijo_b)
            next_generation += [hijo_a, hijo_b]

        population = next_generation

    population = sorted(population,
                        key=lambda genome: fitness_func(genome),
                        reverse=True)

    return population, i



def generar_ciudad(ciudades: int, iteraciones: int) -> Tuple[PoblacionMuestra, int]:
    populations, generation = simular_evolucion(
    populate_func=partial(
        generar_poblacion,ciudades
    ),
    fitness_func=partial(funcion_adecuacion),
    fitness_limit=1,
    generation_limit=iteraciones
    )
    return populations, generation
