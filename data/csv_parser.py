import csv
import colorsys


def rgb_to_hue(r, g, b):
    """Convierte RGB (0-255) a Hue (0-360)"""
    if not r and not g and not b:
        return ''

    r_norm = float(r) / 255.0
    g_norm = float(g) / 255.0
    b_norm = float(b) / 255.0

    h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
    hue = round(h * 360)

    return hue


def binary_search(arr, target):
    """Búsqueda binaria por block_name"""
    left = 0
    right = len(arr) - 1

    while left <= right:
        mid = (left + right) // 2
        mid_name = arr[mid]['block_name']

        if mid_name == target:
            return arr[mid]
        elif mid_name < target:
            left = mid + 1
        else:
            right = mid - 1
    return None


def main():
    # Leer blocks.csv (delimitador: punto y coma)
    print("Leyendo blocks.csv...")
    blocks_data = []
    with open('blocks.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            blocks_data.append(row)

    print(f"  ✓ {len(blocks_data)} bloques leídos")

    # Leer blockmodel_avgs.csv (delimitador: coma)
    print("Leyendo blockmodel_avgs.csv...")
    blockmodel_data = []
    with open('blockmodel_avgs.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            blockmodel_data.append(row)

    # Ordenar alfabéticamente para búsqueda binaria
    blockmodel_data.sort(key=lambda x: x['block_name'])
    print(f"  ✓ {len(blockmodel_data)} bloques de modelo leídos y ordenados")

    # Procesar cada bloque
    print("\nProcesando y combinando datos...")
    merged_data = []
    match_count = 0

    for block_row in blocks_data:
        block_name = block_row.get('block', '').strip()

        # Buscar en blockmodel_avgs
        model_data = binary_search(blockmodel_data, block_name)

        # Calcular hue si hay datos RGB
        hue = ''
        if model_data and model_data.get('r') and model_data.get('g') and model_data.get('b'):
            try:
                r = float(model_data['r'])
                g = float(model_data['g'])
                b = float(model_data['b'])
                hue = rgb_to_hue(r, g, b)
                match_count += 1
            except (ValueError, TypeError):
                pass
        else: print(block_name)

        # Construir fila combinada
        merged_row = {
            'block': block_name,
            'type': block_row.get('type', '').strip(),
            'material': block_row.get('material', '').strip(),
            'processing': block_row.get('processing', '').strip(),
            'categories': block_row.get('categories', '').strip(),
            'biome': block_row.get('biome', '').strip(),
            'r': model_data.get('r', '').strip() if model_data else '',
            'g': model_data.get('g', '').strip() if model_data else '',
            'b': model_data.get('b', '').strip() if model_data else '',
            'a': model_data.get('a', '').strip() if model_data else '',
            'hue': hue
        }

        merged_data.append(merged_row)

    # Escribir CSV de salida
    print(f"  ✓ {match_count}/{len(blocks_data)} bloques tienen datos RGB")
    print("\nEscribiendo blocks_merged.csv...")

    fieldnames = ['block', 'type', 'material', 'processing', 'categories', 'biome',
                  'r', 'g', 'b', 'a', 'hue']

    with open('blocks_merged.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_data)

    print(f"  ✓ Archivo generado exitosamente")
    print(f"\n{'=' * 50}")
    print(f"RESUMEN:")
    print(f"  • Total de bloques: {len(merged_data)}")
    print(f"  • Bloques con RGB/Hue: {match_count}")
    print(f"  • Bloques sin match: {len(merged_data) - match_count}")
    print(f"{'=' * 50}")


if __name__ == '__main__':
    main()