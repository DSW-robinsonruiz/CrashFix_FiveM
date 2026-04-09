# -*- coding: utf-8 -*-
import os
import logging
import json
from datetime import datetime
from typing import Optional

class AdvancedLogger:
    """Sistema de logs avanzado con soporte para JSON y exportación."""
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AdvancedLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_dir: str = 'logs'):
        if hasattr(self, '_initialized'): return
        self._initialized = True
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        self.logger = logging.getLogger("fivem_diagnostic")
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para consola
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)
            
            # Handler para archivo de texto (humano)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.log_file = os.path.join(log_dir, f"crashfix_{timestamp}.log")
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
        
        # Handler para JSON (estructurado)
        self.json_log_file = os.path.join(log_dir, f"crashfix_{timestamp}.json")
        self.json_logs = []

    def log(self, level: int, message: str, extra: Optional[dict] = None):
        """Loguea un mensaje con metadatos extra."""
        self.logger.log(level, message)
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': logging.getLevelName(level),
            'message': message,
            'extra': extra or {}
        }
        self.json_logs.append(log_entry)
        self._save_json_logs()

    def info(self, message: str, extra: Optional[dict] = None):
        self.log(logging.INFO, message, extra)

    def error(self, message: str, extra: Optional[dict] = None):
        self.log(logging.ERROR, message, extra)

    def warning(self, message: str, extra: Optional[dict] = None):
        self.log(logging.WARNING, message, extra)

    def debug(self, message: str, extra: Optional[dict] = None):
        self.log(logging.DEBUG, message, extra)

    def exception(self, message: str, extra: Optional[dict] = None):
        self.log(logging.ERROR, f"EXCEPTION: {message}", extra)

    def _save_json_logs(self):
        """Guarda los logs en formato JSON."""
        try:
            with open(self.json_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.json_logs, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando logs JSON: {e}")

    def export_report(self, output_path: str):
        """Exporta un reporte de diagnóstico reproducible."""
        report = {
            'metadata': {
                'version': '7.0.0-PRO',
                'timestamp': datetime.now().isoformat(),
                'export_file': self.log_file
            },
            'logs': self.json_logs
        }
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.error(f"Error exportando reporte: {e}")
            return False

_app_logger = None

def get_logger(log_dir=None):
    global _app_logger
    if _app_logger is None:
        _app_logger = AdvancedLogger(log_dir)
    return _app_logger.logger

def setup_logging(log_dir: str):
    return get_logger(log_dir)
