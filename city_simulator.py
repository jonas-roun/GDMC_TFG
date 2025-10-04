
from gdpc import Editor, Block
from gdpc.vector_tools import vec3

import utils

cell_size = 5
height, width = 0, 0
buildArea = None
heightmap = None
editor = None
blocks_matrix = None

blocks_values = None
height_values = None
inclination_values = None
buildable_values = None

canvas = None


# ==============================
# Inicialización de mundo
# ==============================
def setup():
    global editor, height, width, buildArea, heightmap, blocks_matrix

    editor = Editor(buffering=True)
    buildArea = editor.getBuildArea()
    editor.loadWorldSlice(cache=True)
    utils.load_block_colors("data/blockmodel_avgs.csv")

    heightmap = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    height, width = heightmap.shape

    # ==============================
    # 1) Guardar bloques en matriz
    # ==============================
    blocks_matrix = [[None for _ in range(width)] for _ in range(height)]
    for x in range(height):
        for y in range(width):
            pos = vec3(buildArea.offset.x + x, heightmap[x][y] - 1, buildArea.offset.z + y)
            bloque = editor.getBlockGlobal(pos)
            blocks_matrix[x][y] = (pos, bloque)


# ==============================
# 2) Precalcular valores de cada modo
# ==============================
def calculate_maps():
    global blocks_values, height_values, inclination_values, buildable_values
    # a) Tipo de bloque
    blocks_values = [[blocks_matrix[x][y][1].id.replace("minecraft:", "") for y in range(width)] for x in range(height)]

    # b) Altura
    height_values = [[blocks_matrix[x][y][0].y for y in range(width)] for x in range(height)]

    # c) Inclinación (gradiente)
    max_h, min_h = heightmap.max(), heightmap.min()
    max_grad = max(1, 8 * (max_h - min_h)) / 2.5
    inclination_values = [[0 for _ in range(width)] for _ in range(height)]

    neighbors = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1), (0, 1),
                 (1, -1), (1, 0), (1, 1)]

    for x in range(height):
        for y in range(width):
            h = height_values[x][y]
            total_diff = 0
            for dx, dy in neighbors:
                nx, ny = x + dx, y + dy
                if 0 <= nx < height and 0 <= ny < width:
                    total_diff += abs(h - height_values[nx][ny])
            inclination_values[x][y] = min(int(255 * (total_diff / max_grad)), 255)

    # d) Edificabilidad
    buildable_values = [[blocks_values[x][y] != "minecraft:water" for y in range(width)] for x in range(height)]

# ==============================
# 3) Función de conversión a color
# ==============================
def value_to_color(mode, x, y):
    if mode == "blocks":
        return utils.get_block_color(blocks_values[x][y])
    elif mode == "height":
        global_min_h = min(map(min, height_values))
        global_max_h = max(map(max, height_values))
        h = height_values[x][y]
        norm = int(255 * (h - global_min_h) / max(1, global_max_h - global_min_h))
        norm = max(0, min(255, norm))
        return f'#{norm:02x}{norm:02x}{norm:02x}'

    elif mode == "inclination":
        norm = inclination_values[x][y]
        if norm <= 63:
            r, g, b = norm, 0, 0
        elif norm <= 128:
            r, g, b = 63, norm - 63, 0
        else:
            r, g, b = 63, 127, norm - 128
        return f'#{r*4:02x}{g*2:02x}{b:02x}'
    elif mode == "buildable":
        return '#FFFFFF' if buildable_values[x][y] else '#000000'
    else:
        return "#000000"

# ==============================
# 4) Función general de dibujo
# ==============================
def draw_map(mode="blocks"):
    global canvas
    canvas.delete("all")
    for x in range(height):
        for y in range(width):
            x1 = x * cell_size
            y1 = y * cell_size
            x2 = (x + 1) * cell_size
            y2 = (y + 1) * cell_size
            color = value_to_color(mode, x, y)
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='')

def refresh_maps():
    setup()
    calculate_maps()
