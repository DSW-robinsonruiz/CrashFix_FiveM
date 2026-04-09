# -*- coding: utf-8 -*-
import unittest
import os
import sys
import json

# Añadir el directorio raíz al path para importar los módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config as cfg
from src.services.diagnostic_service import DiagnosticService
from src.services.repair_service import RepairService
from src.services.hardware_service import HardwareService

class TestCrashFixCore(unittest.TestCase):
    def setUp(self):
        self.diag = DiagnosticService(cfg)
        self.hw = HardwareService(cfg)
        # Mock de sesión para repair service
        class MockSession:
            def __init__(self):
                self.repair_stats = type('Stats', (), {'increment_attempted': lambda: None, 'increment_successful': lambda: None, 'increment_failed': lambda: None})()
                self.report = type('Report', (), {'add_repair_applied': lambda x: None, 'add_repair_failed': lambda x: None})()
        self.repair = RepairService(cfg, MockSession(), dry_run=True)

    def test_pc_tier_profiling(self):
        """Verifica que el perfilado de hardware devuelva una de las categorías válidas."""
        tier = self.hw.profile_pc_tier()
        self.assertIn(tier, ['low', 'medium', 'high'])

    def test_dry_run_safety(self):
        """Verifica que en modo dry-run no se realicen cambios reales (ej. matar procesos)."""
        res = self.repair.kill_fivem_processes()
        self.assertTrue(res['dry_run'])
        self.assertTrue(res['success'])

    def test_crash_classification(self):
        """Verifica la clasificación de crashes basada en errores simulados."""
        mock_crash_info = {
            'Errors': [
                {'Category': 'GPU', 'Severity': 'critical', 'Pattern': 'ERR_GFX_D3D_INIT'}
            ]
        }
        category = self.diag.classify_crash(mock_crash_info)
        self.assertEqual(category, 'GPU')

    def test_error_patterns_exist(self):
        """Verifica que la base de datos de errores tenga patrones cargados."""
        self.assertGreater(len(cfg.error_patterns.patterns), 0)
        self.assertIn('ERR_GFX_D3D_INIT', cfg.error_patterns.patterns)

if __name__ == '__main__':
    unittest.main()
