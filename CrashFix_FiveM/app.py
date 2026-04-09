# -*- coding: utf-8 -*-
"""
FiveM Diagnostic & AUTO-REPAIR Tool v7.0 PRO - Web Version
"""

import os
import sys
import logging
from flask import Flask, render_template, jsonify, request, session
from functools import wraps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config as cfg
from config import (
    server_config,
    system_paths,
    diagnostic_config,
    error_patterns,
    SCRIPT_VERSION,
    get_timestamp,
    BACKUP_CATEGORIES
)

from src.services.session_manager import (
    SessionManager,
    get_session_manager,
    DiagnosticSession
)
from src.services.diagnostic_service import DiagnosticService
from src.services.repair_service import RepairService
from src.services.hardware_service import HardwareService
from src.utils.logging_utils import setup_logging, get_logger
from src.utils.file_utils import ensure_directory_exists

logger = setup_logging(system_paths.work_folder)

app = Flask(__name__)
app.secret_key = server_config.secret_key

# ============= MIDDLEWARE =============

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

def get_current_session() -> DiagnosticSession:
    session_id = session.get('diagnostic_session_id')
    sm = get_session_manager()
    if session_id:
        diag_session = sm.get_session(session_id)
        if diag_session: return diag_session
    diag_session = sm.create_session()
    session['diagnostic_session_id'] = diag_session.session_id
    return diag_session

def api_error_handler(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Unexpected error in {f.__name__}: {e}")
            return jsonify({'error': 'Error interno', 'details': str(e)}), 500
    return decorated_function

# ============= RUTAS PRINCIPALES =============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/diagnostic/full', methods=['POST'])
@api_error_handler
def api_diagnostic_full():
    """Ejecuta un diagnóstico completo e inteligente."""
    diag_session = get_current_session()
    diag = DiagnosticService(cfg)
    hw = HardwareService(cfg)
    
    # 1. Perfilado de Hardware
    hw_info = {
        'gpu': hw.get_gpu_info(),
        'ram': hw.get_ram_info(),
        'cpu': hw.get_cpu_info(),
        'tier': hw.profile_pc_tier(),
        'temps': hw.get_temperatures()
    }
    
    # 2. Análisis de Logs y Crashes
    log_analysis = diag.analyze_fivem_logs()
    crash_category = diag.classify_crash(log_analysis)
    
    # 3. Detección de Conflictos y Mods
    mods = diag.detect_gta_mods()
    conflicts = diag.detect_conflicting_software()
    
    # Actualizar Reporte de Sesión
    report = diag_session.report
    report.hardware_info = hw_info
    report.errors_info = log_analysis
    report.software_info = {'Mods': mods, 'Conflicts': conflicts}
    
    # Motor de Decisiones Automático
    recommendations = []
    if hw_info['temps']['status'] == 'overheating':
        recommendations.append("Detección de sobrecalentamiento: Revisa la ventilación de tu PC.")
    if log_analysis['Found']:
        for err in log_analysis['Errors']:
            recommendations.append(f"Fix recomendado para {err['Pattern']}: {err['Solution']}")
    if mods['Count'] > 0:
        recommendations.append("Se detectaron mods que podrían causar inestabilidad.")
        
    report.recommendations = recommendations
    report.calculate_overall_status()
    
    return jsonify({
        'status': 'completed',
        'hardware': hw_info,
        'crash_category': crash_category,
        'log_analysis': log_analysis,
        'recommendations': recommendations,
        'overall_status': report.status
    })

@app.route('/api/repair/auto', methods=['POST'])
@api_error_handler
def api_repair_auto():
    """Ejecuta la reparación automática inteligente (Botón REPARAR TODO)."""
    diag_session = get_current_session()
    dry_run = request.json.get('dry_run', False)
    repair = RepairService(cfg, diag_session, dry_run=dry_run)
    hw = HardwareService(cfg)
    
    results = []
    
    # 1. Matar procesos
    results.append(repair.kill_fivem_processes())
    
    # 2. Limpiar caché selectiva
    results.append(repair.clear_cache(complete=False))
    
    # 3. Aplicar optimizaciones según hardware
    pc_tier = hw.profile_pc_tier()
    results.append(repair.optimize_system(pc_tier=pc_tier))
    
    return jsonify({
        'status': 'success',
        'dry_run': dry_run,
        'results': results,
        'message': 'Reparación automática completada con éxito'
    })

@app.route('/api/history', methods=['GET'])
@api_error_handler
def api_history():
    """Devuelve el historial de acciones realizadas."""
    diag_session = get_current_session()
    repair = RepairService(cfg, diag_session)
    return jsonify(repair.history)

if __name__ == '__main__':
    ensure_directory_exists(system_paths.work_folder)
    app.run(host=server_config.host, port=server_config.port, debug=server_config.debug)
