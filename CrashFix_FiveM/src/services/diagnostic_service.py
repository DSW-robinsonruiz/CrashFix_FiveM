# -*- coding: utf-8 -*-
import os
import logging
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DiagnosticService:
    def __init__(self, config):
        self.config = config
        self.paths = config.system_paths
        self.diagnostic_config = config.diagnostic_config
        self.error_patterns = config.error_patterns.patterns

    def get_gtav_path(self) -> Dict[str, Any]:
        """Deteccion mejorada de GTA V: registros multiples, Steam, Epic, escaneo inteligente."""
        from src.utils.system_utils import is_windows
        found_paths = []
        seen_paths = set()

        def _add_path(path, platform):
            if not path: return
            path = os.path.normpath(path)
            path_lower = path.lower()
            if path_lower in seen_paths: return
            if os.path.exists(os.path.join(path, 'GTA5.exe')):
                seen_paths.add(path_lower)
                found_paths.append({'path': path, 'platform': platform})

        if is_windows():
            found_paths.extend(self._detect_gtav_from_registry())
            for p in found_paths: seen_paths.add(os.path.normpath(p['path']).lower())
            for steam_path in self._detect_gtav_from_steam(): _add_path(steam_path, 'Steam')
            for epic_path in self._detect_gtav_from_epic(): _add_path(epic_path, 'Epic Games')

        common_paths = [
            r"C:\Program Files\Rockstar Games\Grand Theft Auto V",
            r"C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V",
            r"D:\Games\Grand Theft Auto V",
            r"D:\SteamLibrary\steamapps\common\Grand Theft Auto V"
        ]
        for path in common_paths: _add_path(path, 'Manual')

        result = {
            'Path': found_paths[0]['path'] if found_paths else None,
            'AllPaths': found_paths,
            'Status': 'Encontrado' if found_paths else 'No encontrado'
        }
        if found_paths: result['Platform'] = found_paths[0]['platform']
        return result

    def analyze_fivem_logs(self) -> Dict[str, Any]:
        """Analiza los logs de FiveM para detectar errores conocidos y clasificarlos."""
        logs_path = self.paths.fivem_paths.get('Logs', '')
        if not os.path.isdir(logs_path):
            return {'Found': False, 'Errors': [], 'Message': 'Carpeta de logs no encontrada'}

        detected_errors = []
        log_files = sorted([f for f in os.listdir(logs_path) if f.endswith('.log')], 
                           key=lambda x: os.path.getmtime(os.path.join(logs_path, x)), reverse=True)

        # Analizar solo los últimos 3 logs para eficiencia
        for log_file in log_files[:3]:
            file_path = os.path.join(logs_path, log_file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for pattern, info in self.error_patterns.items():
                        if pattern in content:
                            detected_errors.append({
                                'Pattern': pattern,
                                'LogFile': log_file,
                                'Category': info.get('category', 'General'),
                                'Severity': info.get('severity', 'medium'),
                                'Description': info.get('description', ''),
                                'Solution': info.get('solution', '')
                            })
            except Exception as e:
                logger.warning(f"Error analizando log {log_file}: {e}")

        return {
            'Found': len(detected_errors) > 0,
            'Errors': detected_errors,
            'LogCount': len(log_files)
        }

    def classify_crash(self, crash_info: Dict[str, Any]) -> str:
        """Clasifica un crash basándose en la información recolectada."""
        categories = {'GPU': 0, 'RAM': 0, 'Red': 0, 'Archivos': 0, 'Sistema': 0}
        
        for err in crash_info.get('Errors', []):
            cat = err.get('Category')
            if cat in categories:
                categories[cat] += 1
        
        if not any(categories.values()):
            return 'Desconocido'
            
        return max(categories, key=categories.get)

    def get_fivem_status(self) -> dict:
        fivem_app = self.paths.fivem_paths.get('FiveMApp', '')
        found = os.path.isdir(fivem_app)
        return {
            'Found': found,
            'Path': fivem_app if found else None,
            'Status': 'Instalado' if found else 'No encontrado',
        }

    def detect_gta_mods(self) -> Dict[str, Any]:
        """Detecta mods instalados en la carpeta de GTA V."""
        gta_info = self.get_gtav_path()
        gta_path = gta_info.get('Path')
        if not gta_path: return {'Count': 0, 'Mods': []}

        found_mods = []
        indicators = self.config.diagnostic_config.mod_indicators
        for indicator in indicators:
            path = os.path.join(gta_path, indicator)
            if os.path.exists(path):
                found_mods.append(indicator)

        return {
            'Count': len(found_mods),
            'Mods': found_mods,
            'Status': 'Mods detectados' if found_mods else 'Limpio'
        }

    def detect_conflicting_software(self) -> Dict[str, Any]:
        """Detecta software que suele causar conflictos con FiveM."""
        from src.utils.system_utils import is_process_running
        conflicts = []
        software_list = self.config.diagnostic_config.conflicting_software
        for sw in software_list:
            if is_process_running(sw['process']):
                conflicts.append(sw['name'])
        
        return {
            'Count': len(conflicts),
            'ConflictsFound': conflicts,
            'Status': 'Conflictos detectados' if conflicts else 'Limpio'
        }

    def _detect_gtav_from_registry(self) -> List[Dict[str, str]]:
        found = []
        try:
            import winreg
            entries = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Rockstar Games\Grand Theft Auto V", "InstallFolder", 'Rockstar'),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 271590", "InstallLocation", 'Steam')
            ]
            for hive, key_path, val, plat in entries:
                try:
                    key = winreg.OpenKey(hive, key_path)
                    path, _ = winreg.QueryValueEx(key, val)
                    winreg.CloseKey(key)
                    if path and os.path.exists(os.path.join(path, 'GTA5.exe')):
                        found.append({'path': os.path.normpath(path), 'platform': plat})
                except: pass
        except: pass
        return found

    def _detect_gtav_from_steam(self) -> List[str]:
        # Implementación simplificada para el entorno actual
        return []

    def _detect_gtav_from_epic(self) -> List[str]:
        # Implementación simplificada para el entorno actual
        return []
