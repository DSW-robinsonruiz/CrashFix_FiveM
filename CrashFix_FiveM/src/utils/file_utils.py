# -*- coding: utf-8 -*-
import os, shutil, logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

def get_folder_size(folder: str) -> int:
    total = 0
    try:
        for dirpath, _, filenames in os.walk(folder):
            for filename in filenames:
                try: total += os.path.getsize(os.path.join(dirpath, filename))
                except (OSError, IOError): pass
    except (OSError, IOError): pass
    return total

def validate_path_safety(path: str, allowed_base: str) -> bool:
    try:
        return str(Path(path).resolve()).startswith(str(Path(allowed_base).resolve()))
    except (ValueError, OSError):
        return False

def ensure_directory_exists(directory: str) -> bool:
    if not directory: return False
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except (OSError, IOError) as e:
        logger.error(f"Error creating directory {directory}: {e}")
        return False

def safe_remove_file(filepath: str) -> bool:
    try:
        if os.path.isfile(filepath):
            os.remove(filepath)
            return True
        return False
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Error removing file {filepath}: {e}")
        return False

def safe_remove_directory(directory: str) -> bool:
    """Elimina un directorio de forma robusta, manejando errores de permisos comunes en Windows."""
    import time, stat
    if not os.path.exists(directory):
        return True # Si no existe, objetivo cumplido
    
    if not os.path.isdir(directory):
        return safe_remove_file(directory)
        
    def _make_writable(path):
        try:
            os.chmod(path, stat.S_IWRITE)
        except (OSError, PermissionError) as e:
            logger.debug(f"No se pudo cambiar permisos de {path}: {e}")

    def _rmtree_recursive(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                filepath = os.path.join(root, name)
                _make_writable(filepath)
                try:
                    os.remove(filepath)
                except (OSError, PermissionError) as e:
                    logger.warning(f"No se pudo eliminar archivo {filepath}: {e}")
            for name in dirs:
                dirpath = os.path.join(root, name)
                _make_writable(dirpath)
                try:
                    os.rmdir(dirpath)
                except (OSError, PermissionError) as e:
                    logger.warning(f"No se pudo eliminar directorio {dirpath}: {e}")
        _make_writable(path)
        try:
            os.rmdir(path)
        except (OSError, PermissionError) as e:
            logger.warning(f"No se pudo eliminar directorio raiz {path}: {e}")

    # Intentar hasta 3 veces con pequeñas esperas
    for attempt in range(3):
        try:
            if not os.path.exists(directory): return True
            shutil.rmtree(directory, ignore_errors=True)
            if not os.path.exists(directory): return True
            
            # Si shutil falló, intentar borrado manual agresivo
            _rmtree_recursive(directory)
            if not os.path.exists(directory): return True
            
            time.sleep(0.5) # Esperar a que Windows libere handles
        except (OSError, PermissionError) as e:
            logger.warning(f"Intento {attempt + 1}/3 de eliminar {directory} fallo: {e}")
            time.sleep(0.5)
            
    still_exists = os.path.exists(directory)
    if still_exists:
        logger.error(f"No se pudo eliminar {directory} despues de 3 intentos")
    return not still_exists

def backup_item(source: str, backup_name: str, backup_folder: str, category: str = 'General', timestamp: Optional[str] = None) -> Optional[str]:
    if not os.path.exists(source): return None
    if timestamp is None:
        from config import get_timestamp
        timestamp = get_timestamp()
    category_folder = os.path.join(backup_folder, category)
    if not ensure_directory_exists(category_folder): return None
    backup_path = os.path.join(category_folder, f"{backup_name}_{timestamp}")
    try:
        if os.path.isdir(source):
            shutil.copytree(source, backup_path)
        else:
            ext = os.path.splitext(source)[1]
            backup_path = f"{backup_path}{ext}"
            shutil.copy2(source, backup_path)
        return backup_path
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Error creating backup of {source}: {e}")
        return None
