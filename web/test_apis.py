"""
Script de verificación de APIs en tiempo real
Ejecutar: python web/test_apis.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from apis_realtime import (
    MinisterioSaludAPI,
    SenamhiAPI,
    get_realtime_external_factors
)
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def print_separator(title=""):
    print("\n" + "="*70)
    if title:
        print(f"  {title}")
        print("="*70)
    print()

def test_covid():
    """Probar API de COVID"""
    print_separator("TEST 1: DATOS COVID-19")
    
    departamentos_test = ['LIMA', 'AREQUIPA', 'CUSCO', 'PIURA']
    
    print("📊 Intensidad COVID por Departamento:\n")
    
    results = []
    for dept in departamentos_test:
        intensity = MinisterioSaludAPI.get_covid_intensity_by_department(dept)
        results.append((dept, intensity))
        
        # Emoji visual
        if intensity < 0.3:
            emoji = "🟢"
        elif intensity < 0.6:
            emoji = "🟡"
        else:
            emoji = "🔴"
        
        print(f"  {emoji} {dept:15s}: {intensity*100:5.1f}% intensidad")
    
    print(f"\n✅ Promedio nacional: {sum(r[1] for r in results)/len(results)*100:.1f}%")
    
    return True

def test_temperatura():
    """Probar API de Temperatura"""
    print_separator("TEST 2: TEMPERATURA")
    
    departamentos_test = ['LIMA', 'AREQUIPA', 'LORETO', 'PUNO', 'PIURA']
    
    print("🌡️ Anomalías de Temperatura:\n")
    
    for dept in departamentos_test:
        anomalia = SenamhiAPI.get_temperature_anomaly(dept)
        temp_promedio = SenamhiAPI._get_historical_average(dept)
        temp_actual = temp_promedio + anomalia
        
        # Emoji visual
        if anomalia > 1:
            emoji = "🔥"
        elif anomalia < -1:
            emoji = "❄️"
        else:
            emoji = "🌤️"
        
        print(f"  {emoji} {dept:15s}: {temp_actual:5.1f}°C (promedio: {temp_promedio:.1f}°C, anomalía: {anomalia:+.1f}°C)")
    
    print("\n✅ Datos de temperatura OK")
    
    return True

def test_integracion():
    """Probar integración completa"""
    print_separator("TEST 3: INTEGRACIÓN COMPLETA")
    
    departamentos_test = ['LIMA', 'AREQUIPA', 'CUSCO']
    
    print("🌍 Factores Externos Combinados:\n")
    
    for dept in departamentos_test:
        factores = get_realtime_external_factors(departamento=dept)
        
        print(f"  📍 {dept}:")
        print(f"     COVID:       {factores['covid_intensity']*100:5.1f}%")
        print(f"     Temperatura: {factores['temperatura_anomalia']:+.2f}°C")
        print(f"     Timestamp:   {factores['timestamp'][:19]}")
        print()
    
    print("✅ Integración completa funcionando")
    
    return True

def test_mapa_covid():
    """Probar datos para mapa de COVID"""
    print_separator("TEST 4: DATOS PARA MAPA COVID")
    
    stats = MinisterioSaludAPI.get_all_departments_stats()
    
    print(f"📊 Estadísticas de {len(stats)} departamentos:\n")
    
    # Top 5 más afectados
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['intensidad'], reverse=True)[:5]
    
    print("  Top 5 departamentos más afectados:")
    for i, (dept, data) in enumerate(sorted_stats, 1):
        print(f"    {i}. {dept:15s}: {data['casos_totales']:,} casos ({data['intensidad']*100:.1f}%)")
    
    print(f"\n✅ Datos de mapa disponibles")
    
    return True

def test_mapa_temperatura():
    """Probar datos para mapa de temperatura"""
    print_separator("TEST 5: DATOS PARA MAPA TEMPERATURA")
    
    temp_data = SenamhiAPI.get_temperature_map_data()
    
    print(f"🌡️ Datos de temperatura para {len(temp_data)} departamentos\n")
    
    # Departamentos más cálidos y más fríos
    sorted_temps = sorted(temp_data.items(), key=lambda x: x[1]['anomalia'], reverse=True)
    
    print("  🔥 Más cálidos (anomalía positiva):")
    for dept, data in sorted_temps[:3]:
        print(f"    {dept:15s}: {data['anomalia']:+.2f}°C")
    
    print("\n  ❄️ Más fríos (anomalía negativa):")
    for dept, data in sorted_temps[-3:]:
        print(f"    {dept:15s}: {data['anomalia']:+.2f}°C")
    
    print(f"\n✅ Datos de temperatura para mapa OK")
    
    return True

def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n" + "🧪 INICIANDO PRUEBAS DE APIS EN TIEMPO REAL".center(70))
    
    tests = [
        ("COVID-19", test_covid),
        ("Temperatura", test_temperatura),
        ("Integración", test_integracion),
        ("Mapa COVID", test_mapa_covid),
        ("Mapa Temperatura", test_mapa_temperatura)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ Test {name} falló: {e}")
            failed += 1
    
    # Resumen final
    print_separator("RESUMEN")
    
    total = passed + failed
    print(f"  Tests ejecutados: {total}")
    print(f"  ✅ Exitosos: {passed}")
    print(f"  ❌ Fallidos: {failed}")
    
    if failed == 0:
        print(f"\n  🎉 ¡TODOS LOS TESTS PASARON!")
        print(f"  🚀 El sistema está listo para usar")
    else:
        print(f"\n  ⚠️ Algunos tests fallaron")
        print(f"  💡 Revisa los errores arriba")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    run_all_tests()