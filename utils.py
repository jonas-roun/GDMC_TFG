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
