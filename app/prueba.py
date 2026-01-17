import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.dgii_service import DGIIService

# Test con cédula de ejemplo
result = DGIIService.validate_and_get_info("22900047923", "cedula")
print("Resultado de la consulta DGII:")
print("-" * 50)
print(f"Éxito: {result.get('success')}")
print(f"Mensaje: {result.get('message', result.get('error', 'Sin mensaje'))}")
print(f"Modo validación: {result.get('validation_mode')}")

if result.get('success') and result.get('data'):
    print("\nDatos obtenidos:")
    print(f"  Nombre: {result.get('data', {}).get('first_name', '')} {result.get('data', {}).get('last_name', '')}")
    print(f"  Nombre completo: {result.get('data', {}).get('full_name', '')}")
    print(f"  Estado: {result.get('data', {}).get('status', '')}")