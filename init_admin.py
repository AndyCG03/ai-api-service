"""
Script para inicializar el sistema de API Keys y crear el primer admin.

Uso:
    python scripts/init_admin.py
"""

import sys
import getpass
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.auth.api_keys import api_key_manager
from loguru import logger


def create_admin_key(name: str, description: str, expires_in_days: int = None) -> str:
    """Crea una API key de administrador."""
    return api_key_manager.create_key(
        name=name,
        description=description,
        expires_in_days=expires_in_days,
        rate_limit=1000,  # Rate limit alto para admin
        allowed_endpoints=["*"],  # Acceso completo
        is_admin=True
    )


def display_admin_key(api_key: str, key_info: dict):
    """Muestra la API key de forma segura."""
    key_prefix = api_key[:12]
    
    print("\n" + "="*60)
    print("✅ API KEY DE ADMINISTRADOR CREADA EXITOSAMENTE")
    print("="*60)
    
    print(f"\n📋 Información:")
    print(f"   Nombre: {key_info['name']}")
    print(f"   Descripción: {key_info['description'] or 'N/A'}")
    print(f"   Prefijo: {key_prefix}...")
    print(f"   Creada: {key_info['created_at']}")
    print(f"   Expira: {key_info['expires_at'] or 'Nunca'}")
    print(f"   Rate Limit: {key_info['rate_limit']}/min")
    print(f"   Es Admin: {'✅ Sí' if key_info['is_admin'] else '❌ No'}")
    
    print(f"\n🔑 API Key: \033[92m{api_key}\033[0m")
    
    print("\n" + "="*60)
    print("⚠️  ADVERTENCIAS DE SEGURIDAD:")
    print("="*60)
    print("   1. ⚠️  Guarda esta key de forma SEGURA (password manager recomendado)")
    print("   2. ⚠️  NO la compartas con nadie")
    print("   3. ⚠️  NO podrás volver a verla completa después de ahora")
    print("   4. ⚠️  NO la guardes en código fuente o repositorios públicos")
    print("   5. ⚠️  Si la pierdes, deberás revocarla y crear una nueva")
    print("="*60)
    
    print("\n💡 Ejemplo de uso inmediato:")
    print("   # Listar todas las API keys existentes")
    print(f"   curl -X GET 'http://localhost:8000/v1/admin/keys/list' \\")
    print("     -H 'X-API-Key: " + api_key + "'")
    
    print("\n🛠️  Para crear una key para cliente:")
    print("   curl -X POST 'http://localhost:8000/v1/admin/keys/create' \\")
    print(f"     -H 'X-API-Key: {api_key}' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{")
    print('       "name": "Cliente Ejemplo",')
    print('       "description": "Key para cliente de prueba",')
    print('       "expires_in_days": 90,')
    print('       "rate_limit": 60,')
    print('       "allowed_endpoints": ["/generate/chat", "/transcribe/"],')
    print('       "is_admin": false')
    print("     }'")


def save_to_file(api_key: str, key_info: dict):
    """Guarda la API key en un archivo seguro."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    admin_file = Path(f".admin_key_{timestamp}.txt")
    
    content = f"""# API KEY DE ADMINISTRADOR
# ================================
# ⚠️ ADVERTENCIA: Este archivo contiene información sensible
# No lo subas a repositorios públicos ni lo compartas
# ================================
Fecha de creación: {key_info['created_at']}
Nombre: {key_info['name']}
Descripción: {key_info['description']}
Prefijo: {api_key[:12]}...
Expira: {key_info['expires_at'] or 'Nunca'}
Es Admin: {'Sí' if key_info['is_admin'] else 'No'}
Rate Limit: {key_info['rate_limit']}/min

API KEY COMPLETA:
{api_key}

# Ejemplos de uso:
# curl -H "X-API-Key: {api_key}" http://localhost:8000/v1/admin/keys/list

# Revocar esta key si es comprometida:
# curl -X POST http://localhost:8000/v1/admin/keys/revoke \\
#   -H "X-API-Key: [OTRA_KEY_ADMIN]" \\
#   -H "Content-Type: application/json" \\
#   -d '{{"key_prefix": "{api_key[:12]}..."}}'
"""
    
    try:
        with open(admin_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Hacer el archivo solo readable por el usuario (Linux/Mac)
        try:
            import os
            os.chmod(admin_file, 0o600)
        except:
            pass
            
        print(f"\n📁 Key guardada en: \033[93m{admin_file.absolute()}\033[0m")
        print("   ⚠️  Este archivo NO está en .gitignore, muévelo a un lugar seguro\n")
        
        # Crear .gitignore si no existe
        gitignore = Path(".gitignore")
        if not gitignore.exists():
            with open(gitignore, "w", encoding="utf-8") as f:
                f.write("# Archivos de API Keys\n")
                f.write(".admin_key_*.txt\n")
                f.write(".env.admin\n")
            print("✅ .gitignore creado automáticamente\n")
            
    except Exception as e:
        print(f"⚠️  No se pudo guardar en archivo: {e}")


def confirm_action(message: str) -> bool:
    """Pide confirmación al usuario."""
    print(f"\n{message} (s/n): ", end="", flush=True)
    response = input().strip().lower()
    return response in ['s', 'si', 'sí', 'y', 'yes']


def main():
    """Inicializa el sistema y crea la primera API key de administrador."""
    
    print("\n" + "="*60)
    print("🚀 INICIALIZACIÓN DEL SISTEMA DE API KEYS")
    print("="*60)
    
    # Verificar si la base de datos existe
    db_path = Path("./data/api_keys.db")
    if db_path.exists():
        print(f"\n📊 Base de datos encontrada: {db_path}")
        print(f"   Tamaño: {db_path.stat().st_size / 1024:.1f} KB")
    else:
        print("\n🆕 Base de datos no encontrada, se creará automáticamente")
    
    print("\n" + "="*60)
    print("🔍 VERIFICANDO ADMINISTRADORES EXISTENTES")
    print("="*60)
    
    try:
        keys = api_key_manager.list_keys()
        admin_keys = [k for k in keys if k['is_admin']]
        
        if admin_keys:
            print(f"\n📋 Se encontraron {len(admin_keys)} admin(s) existente(s):")
            for i, key in enumerate(admin_keys, 1):
                status_icon = "✅" if key['is_active'] else "🔒"
                status_text = "ACTIVA" if key['is_active'] else "REVOCADA"
                print(f"\n   {i}. {key['key_prefix']}...")
                print(f"      📝 Nombre: {key['name']}")
                print(f"      📅 Creada: {key['created_at']}")
                print(f"      📊 Uso: {key['usage_count']} requests")
                print(f"      🔧 Estado: {status_icon} {status_text}")
            
            if not confirm_action("\n¿Deseas crear una nueva key de administrador?"):
                print("\n👋 Operación cancelada")
                return 0
    except Exception as e:
        print(f"⚠️  Error al verificar keys existentes: {e}")
        print("   Continuando con la creación de una nueva key...")
    
    print("\n" + "="*60)
    print("📝 CONFIGURACIÓN DE NUEVA API KEY")
    print("="*60)
    
    # Obtener datos del usuario
    print("\n📝 Información de la nueva API Key:")
    
    default_name = "Admin Principal"
    name = input(f"   Nombre [{default_name}]: ").strip()
    if not name:
        name = default_name
    
    description = input("   Descripción (opcional): ").strip()
    
    # Expiración
    print("\n⏰ Configuración de expiración:")
    print("   Presiona Enter para SIN EXPIRACIÓN (recomendado para admin)")
    print("   O ingresa el número de días (ej: 90, 365)")
    
    while True:
        days_input = input("   Días hasta expiración: ").strip()
        if not days_input:
            expires_in_days = None
            break
        
        try:
            expires_in_days = int(days_input)
            if expires_in_days <= 0:
                print("   ⚠️  El número debe ser mayor a 0")
                continue
            break
        except ValueError:
            print("   ⚠️  Ingresa un número válido o presiona Enter")
    
    # Confirmación final
    print("\n" + "="*60)
    print("📋 RESUMEN DE CONFIGURACIÓN")
    print("="*60)
    print(f"   Nombre: {name}")
    print(f"   Descripción: {description or '(sin descripción)'}")
    print(f"   Expiración: {'Nunca' if not expires_in_days else f'{expires_in_days} días'}")
    print(f"   Rate Limit: 1000 requests/minuto")
    print(f"   Acceso: Todos los endpoints (*)")
    print(f"   Rol: Administrador (puede crear/revocar otras keys)")
    
    if not confirm_action("\n¿Confirmas la creación de esta API key?"):
        print("\n👋 Operación cancelada")
        return 0
    
    # Crear la key
    try:
        print("\n🔄 Creando API Key...")
        api_key = create_admin_key(name, description, expires_in_days)
        
        # Obtener información de la key recién creada
        keys = api_key_manager.list_keys()
        new_key = next((k for k in keys if k['key_prefix'] == api_key[:12]), None)
        
        if not new_key:
            raise ValueError("No se pudo obtener información de la key creada")
        
        # Mostrar información
        display_admin_key(api_key, new_key)
        
        # Preguntar si guardar en archivo
        if confirm_action("\n¿Deseas guardar esta key en un archivo de texto?"):
            save_to_file(api_key, new_key)
        else:
            print("\n⚠️  La key NO se ha guardado en archivo.")
            print("   Asegúrate de copiarla y guardarla en un lugar seguro.")
        
        print("\n" + "="*60)
        print("🎉 ¡CONFIGURACIÓN COMPLETADA!")
        print("="*60)
        print("\n✅ El sistema de API Keys está listo para usar.")
        print("✅ Puedes comenzar a crear keys para clientes usando la API.")
        print(f"✅ Usa esta key para autenticarte: \033[92m{api_key}\033[0m")
        
    except Exception as e:
        logger.error(f"❌ Error creando API key: {e}")
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Operación cancelada por el usuario")
        sys.exit(0)