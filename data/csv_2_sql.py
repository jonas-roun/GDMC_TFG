import sqlite3
import csv


def crear_base_datos():
    """
    Crea una base de datos SQLite desde blocks_merged.csv
    con índices optimizados para búsquedas semánticas.
    """

    # Conectar/crear BD
    conn = sqlite3.connect('blocks.db')
    cursor = conn.cursor()

    # Crear tabla
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS blocks
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       block
                       TEXT
                       NOT
                       NULL
                       UNIQUE,
                       type
                       TEXT,
                       material
                       TEXT,
                       processing
                       TEXT,
                       categories
                       TEXT,
                       biome
                       TEXT,
                       r
                       REAL,
                       g
                       REAL,
                       b
                       REAL,
                       a
                       REAL,
                       hue
                       REAL
                   )
                   ''')

    # Leer CSV e insertar datos
    print("Importando bloques desde blocks_merged.csv...")
    with open('blocks_merged.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convertir valores vacíos a NULL
            valores = {
                'block': row['block'],
                'type': row['type'] or None,
                'material': row['material'] or None,
                'processing': row['processing'] or None,
                'categories': row['categories'] or None,
                'biome': row['biome'] or None,
                'r': float(row['r']) if row['r'] else None,
                'g': float(row['g']) if row['g'] else None,
                'b': float(row['b']) if row['b'] else None,
                'a': float(row['a']) if row['a'] else None,
                'hue': float(row['hue']) if row['hue'] else None
            }

            cursor.execute('''
                           INSERT
                           OR IGNORE INTO blocks 
                (block, type, material, processing, categories, biome, r, g, b, a, hue)
                VALUES (:block, :type, :material, :processing, :categories, :biome, :r, :g, :b, :a, :hue)
                           ''', valores)

    # Crear índices para búsquedas rápidas
    print("Creando índices...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON blocks(type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_material ON blocks(material)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_categories ON blocks(categories)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hue ON blocks(hue)')

    conn.commit()

    # Estadísticas
    cursor.execute('SELECT COUNT(*) FROM blocks')
    total = cursor.fetchone()[0]
    print(f"✓ Base de datos creada: {total} bloques importados")

    conn.close()


if __name__ == '__main__':
    crear_base_datos()