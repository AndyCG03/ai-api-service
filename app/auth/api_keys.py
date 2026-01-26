# app/auth/api_keys.py (contenido completo)

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path
import sqlite3
from loguru import logger
from fastapi import Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader

from app.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyManager:
    """Gestor de API Keys con almacenamiento seguro en SQLite."""
    
    def __init__(self, db_path: str = "./data/api_keys.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate_db()
        self._init_db()
    
    def _migrate_db(self):
        """Migra la base de datos existente si es necesario."""
        with sqlite3.connect(self.db_path) as conn:
            # Verificar si la tabla existe
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='api_keys'
            """)
            
            if cursor.fetchone():
                # La tabla existe, verificar si tiene la columna is_admin
                try:
                    cursor = conn.execute("SELECT is_admin FROM api_keys LIMIT 1")
                    logger.info("✅ Base de datos ya tiene columna is_admin")
                except sqlite3.OperationalError:
                    # La columna no existe, agregarla
                    logger.info("🔄 Migrando base de datos: agregando columna is_admin...")
                    conn.execute("ALTER TABLE api_keys ADD COLUMN is_admin BOOLEAN DEFAULT 0")
                    conn.commit()
                    logger.success("✅ Columna is_admin agregada exitosamente")
            else:
                logger.info("🆕 Base de datos no existe, se creará desde cero")
    
    def _init_db(self):
        """Inicializa la base de datos con las tablas necesarias."""
        with sqlite3.connect(self.db_path) as conn:
            # Tabla principal de API Keys (se crea solo si no existe)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_hash TEXT UNIQUE NOT NULL,
                    key_prefix TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    rate_limit INTEGER DEFAULT 60,
                    allowed_endpoints TEXT,
                    last_used_at TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    is_admin BOOLEAN DEFAULT 0
                )
            """)
            
            # Tabla de logs
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_key_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_prefix TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_key_hash ON api_keys(key_hash)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON api_key_logs(timestamp)
            """)
            
            conn.commit()
            logger.info("✅ Base de datos de API Keys inicializada")
    
    @staticmethod
    def _hash_key(api_key: str) -> str:
        """Hash seguro de la API key usando SHA-256."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def generate_key() -> str:
        """
        Genera una API key segura.
        Formato: ai_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (48 caracteres)
        """
        random_part = secrets.token_urlsafe(32)
        return f"ai_{random_part}"
    
    def create_key(
        self,
        name: str,
        description: str = "",
        expires_in_days: Optional[int] = None,
        rate_limit: int = 60,
        allowed_endpoints: Optional[List[str]] = None,
        is_admin: bool = False
    ) -> str:
        """
        Crea una nueva API key.
        
        Returns:
            str: La API key en texto plano (solo se muestra una vez)
        """
        api_key = self.generate_key()
        key_hash = self._hash_key(api_key)
        key_prefix = api_key[:12]  # ai_xxxxxxxx para identificación
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        endpoints_str = ",".join(allowed_endpoints) if allowed_endpoints else "*"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO api_keys 
                (key_hash, key_prefix, name, description, expires_at, 
                 rate_limit, allowed_endpoints, is_admin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                key_hash, key_prefix, name, description, 
                expires_at, rate_limit, endpoints_str, is_admin
            ))
            conn.commit()
        
        logger.info(f"✅ API Key creada: {key_prefix}... para '{name}' (admin: {is_admin})")
        return api_key
    
    def validate_key(
        self, 
        api_key: str, 
        endpoint: str = "*",
        require_admin: bool = False
    ) -> dict:
        """
        Valida una API key y retorna información sobre ella.
        
        Args:
            require_admin: Si es True, solo acepta claves de administrador
        
        Raises:
            HTTPException: Si la key es inválida
        """
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key missing"
            )
        
        key_hash = self._hash_key(api_key)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM api_keys 
                WHERE key_hash = ? AND is_active = 1
            """, (key_hash,))
            
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"❌ API Key inválida intentada: {api_key[:12]}...")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API Key"
                )
            
            key_data = dict(row)
            
            # Verificar si es administrador (si se requiere)
            if require_admin and not key_data.get('is_admin'):
                logger.warning(f"❌ Intento de acceso admin con key no-admin: {key_data['key_prefix']}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin privileges required"
                )
            
            # Verificar expiración
            if key_data['expires_at']:
                expires_at = datetime.fromisoformat(key_data['expires_at'])
                if datetime.now() > expires_at:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="API Key expired"
                    )
            
            # Verificar endpoints permitidos
            allowed = key_data['allowed_endpoints']
            if allowed != "*" and endpoint not in allowed.split(","):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API Key not authorized for endpoint: {endpoint}"
                )
            
            # Actualizar último uso
            conn.execute("""
                UPDATE api_keys 
                SET last_used_at = CURRENT_TIMESTAMP, usage_count = usage_count + 1
                WHERE key_hash = ?
            """, (key_hash,))
            conn.commit()
            
            return key_data
    
    def log_request(
        self, 
        key_prefix: str, 
        endpoint: str, 
        method: str,
        status_code: int,
        ip_address: str
    ):
        """Registra el uso de una API key."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO api_key_logs 
                (key_prefix, endpoint, method, status_code, ip_address)
                VALUES (?, ?, ?, ?, ?)
            """, (key_prefix, endpoint, method, status_code, ip_address))
            conn.commit()
    
    def revoke_key(self, key_prefix: str) -> bool:
        """Revoca una API key."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE api_keys SET is_active = 0 
                WHERE key_prefix = ?
            """, (key_prefix,))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"🔒 API Key revocada: {key_prefix}")
                return True
            return False
    
    def activate_key(self, key_prefix: str) -> bool:
        """Activa una API key previamente revocada."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE api_keys SET is_active = 1 
                WHERE key_prefix = ?
            """, (key_prefix,))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"✅ API Key activada: {key_prefix}")
                return True
            return False
    
    def list_keys(self, active_only: bool = False) -> List[dict]:
        """Lista todas las API keys (sin mostrar el hash completo)."""
        query = """
            SELECT id, key_prefix, name, description, created_at, 
                   expires_at, is_active, rate_limit, allowed_endpoints,
                   last_used_at, usage_count, is_admin
            FROM api_keys
        """
        
        if active_only:
            query += " WHERE is_active = 1"
        
        query += " ORDER BY created_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_key_stats(self, key_prefix: Optional[str] = None) -> dict:
        """Obtiene estadísticas de uso."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if key_prefix:
                # Estadísticas específicas de una key
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_requests,
                        COUNT(DISTINCT endpoint) as unique_endpoints,
                        MIN(timestamp) as first_request,
                        MAX(timestamp) as last_request
                    FROM api_key_logs 
                    WHERE key_prefix = ?
                """, (key_prefix,))
                
                stats = dict(cursor.fetchone())
                
                # Agregar info de la key
                cursor = conn.execute("""
                    SELECT usage_count, created_at, is_active, is_admin
                    FROM api_keys 
                    WHERE key_prefix = ?
                """, (key_prefix,))
                
                key_info = cursor.fetchone()
                if key_info:
                    stats.update(dict(key_info))
                
                return stats
            else:
                # Estadísticas globales
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_keys,
                        SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_keys,
                        SUM(CASE WHEN is_admin = 1 THEN 1 ELSE 0 END) as admin_keys,
                        SUM(usage_count) as total_requests,
                        COUNT(DISTINCT key_prefix) as keys_used
                    FROM api_keys
                """)
                
                return dict(cursor.fetchone())


# Instancia global
api_key_manager = APIKeyManager()


# Dependencia para FastAPI - Para claves normales
async def verify_api_key(
    request: Request,
    api_key: str = Security(API_KEY_HEADER)
) -> dict:
    """
    Dependencia de FastAPI para validar API keys normales.
    
    Usage:
        @app.get("/protected")
        async def protected_route(key_data: dict = Depends(verify_api_key)):
            return {"message": f"Hello {key_data['name']}"}
    """
    endpoint = request.url.path
    key_data = api_key_manager.validate_key(api_key, endpoint, require_admin=False)
    
    # Log asíncrono (opcional, no bloquea la request)
    try:
        api_key_manager.log_request(
            key_prefix=key_data['key_prefix'],
            endpoint=endpoint,
            method=request.method,
            status_code=200,
            ip_address=request.client.host if request.client else "unknown"
        )
    except Exception as e:
        logger.error(f"Error logging request: {e}")
    
    return key_data


# Dependencia para FastAPI - Para claves de administrador
async def verify_admin_key(
    request: Request,
    api_key: str = Security(API_KEY_HEADER)
) -> dict:
    """
    Dependencia de FastAPI para validar API keys de administrador.
    
    Usage:
        @app.get("/admin-only")
        async def admin_route(admin_data: dict = Depends(verify_admin_key)):
            return {"message": f"Hello admin {admin_data['name']}"}
    """
    endpoint = request.url.path
    key_data = api_key_manager.validate_key(api_key, endpoint, require_admin=True)
    
    # Log asíncrono para operaciones admin
    try:
        api_key_manager.log_request(
            key_prefix=key_data['key_prefix'],
            endpoint=endpoint,
            method=request.method,
            status_code=200,
            ip_address=request.client.host if request.client else "unknown"
        )
    except Exception as e:
        logger.error(f"Error logging admin request: {e}")
    
    return key_data