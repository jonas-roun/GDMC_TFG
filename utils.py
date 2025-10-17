import pandas as pd

block_color = {}

def calcular_inclinacion(x, y, blocks_matrix, height, width, max_grad):
    """
    Calcula la inclinación de un bloque basado en la altura de sus vecinos.
    Devuelve un entero entre 0 y 255.
    """
    h, total_diff = blocks_matrix[x][y][0].y, 0  # pos.y
    # Vecinos en las 8 direcciones
    neighbors = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0), (1, 1),
    ]
    for dx, dy in neighbors:
        nx, ny = x + dx, y + dy
        if 0 <= nx < height and 0 <= ny < width:
            npos, _ = blocks_matrix[nx][ny]
            total_diff += abs(h - npos.y)

    # Normalizar entre 0 y 255
    norm = min(int(255 * (total_diff / max_grad)), 255)
    return norm

def load_block_colors(csv_path, include_alpha=False):
    """
    Lee un CSV con columnas (block_name, r, g, b, a) y devuelve
    un diccionario {block_name: "#RRGGBB"} o "#RRGGBBAA" si include_alpha=True.
    """
    global block_color
    df = pd.read_csv(csv_path)

    for _, row in df.iterrows():
        r, g, b, a = int(row['r']), int(row['g']), int(row['b']), int(row['a'])
        if include_alpha:
            hex_color = "#{:02X}{:02X}{:02X}{:02X}".format(r, g, b, a)
        else:
            hex_color = "#{:02X}{:02X}{:02X}".format(r, g, b)
        block_color[row['block_name']] = hex_color

def get_block_color(block_name: str) -> str:
    if block_name == "grass_block":
        return "#4ADB48"
    elif block_name == "water":
        return "#1d8df0"
    return block_color[block_name]
