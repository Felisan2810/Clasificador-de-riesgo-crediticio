from pathlib import Path

# Configuración
ARCHIVO_ENTRADA = Path("Data/raw/dataset_credito.csv")
ARCHIVO_SALIDA = Path("Data/raw/dataset_credito1.csv")

print(f"🔧 Reparando archivo: {ARCHIVO_ENTRADA}")

try:
    with open(ARCHIVO_ENTRADA, 'r', encoding='utf-8') as fin:
        lineas = fin.readlines()
except UnicodeDecodeError:
    print("   ⚠️ UTF-8 falló, intentando con Latin-1...")
    with open(ARCHIVO_ENTRADA, 'r', encoding='latin-1') as fin:
        lineas = fin.readlines()

print(f"   Leídas {len(lineas):,} líneas.")

# Limpieza: Quitamos las comillas dobles (") de cada línea
lineas_limpias = []
for linea in lineas:
    # Quitamos espacios y saltos de linea al inicio/final
    linea_temp = linea.strip()
    
    # Si la línea empieza y termina con comillas, las quitamos
    if linea_temp.startswith('"') and linea_temp.endswith('"'):
        linea_temp = linea_temp[1:-1]
    
    linea_temp = linea_temp.replace('"', '')
    
    lineas_limpias.append(linea_temp + "\n")

# Guardar archivo nuevo
with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as fout:
    fout.writelines(lineas_limpias)

print(f"✅ Archivo reparado guardado en: {ARCHIVO_SALIDA}")
print("🚀 AHORA: Actualiza tu config.py para usar 'dataset_credito_limpio.csv'")