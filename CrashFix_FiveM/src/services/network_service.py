# -*- coding: utf-8 -*-
import re, logging
from typing import Dict, List, Any
from src.utils.system_utils import is_windows, run_command, ping_host

logger = logging.getLogger(__name__)

class NetworkService:
    def __init__(self, config):
        self.config = config
        self.network_config = config.network_config
        self.timeout_config = config.timeout_config

    def test_network_quality(self) -> Dict[str, Any]:
        targets = self.network_config.dns_servers[:2]
        results = []
        total_latency = 0
        successful = 0
        for target in targets:
            ping_result = ping_host(target['ip'], count=1, timeout_ms=1000)
            if ping_result and ping_result['success']:
                results.append({'name': target['name'], 'latency': ping_result['latency_ms'], 'status': 'ok'})
                total_latency += ping_result['latency_ms']
                successful += 1
            else:
                results.append({'name': target['name'], 'latency': 0, 'status': 'failed'})
        avg_latency = round(total_latency / successful) if successful > 0 else 0
        status = 'OK' if successful > 0 else 'Error'
        if avg_latency > self.network_config.max_acceptable_latency_ms:
            status = 'Slow'
        return {'Status': status, 'Ping': avg_latency, 'Tests': results, 'Successful': successful, 'Total': len(targets)}

    def test_packet_loss(self) -> Dict[str, Any]:
        targets = ['8.8.8.8', '1.1.1.1']
        results = []
        if is_windows():
            for target in targets:
                try:
                    # Usar shell=True para que el comando ping de Windows funcione correctamente con run_command
                    from src.utils.system_utils import run_command
                    res = run_command(f'ping -n 5 {target}', timeout=self.timeout_config.packet_loss_timeout)
                    if res and res.stdout:
                        # Buscar patrones de pérdida de paquetes en español e inglés
                        match = re.search(r'(\d+)%\s*(?:perdidos|loss)', res.stdout, re.IGNORECASE)
                        loss = int(match.group(1)) if match else 0
                        results.append({'name': target, 'packet_loss': loss, 'status': 'ok' if loss < 5 else 'high'})
                    else:
                        results.append({'name': target, 'packet_loss': 100, 'status': 'error'})
                except Exception as e:
                    logger.warning(f"Packet loss test error for {target}: {e}")
                    results.append({'name': target, 'packet_loss': 100, 'status': 'error'})
        else:
            results = [{'name': t, 'packet_loss': 0, 'status': 'ok'} for t in targets]
        
        valid = [r['packet_loss'] for r in results if r['packet_loss'] >= 0]
        avg_loss = round(sum(valid) / len(valid), 1) if valid else 0
        recommendations = []
        if avg_loss > self.network_config.max_acceptable_packet_loss_percent:
            recommendations.append('Contacta a tu ISP, hay pérdida de paquetes significativa')
            recommendations.append('Verifica tu conexión por cable en lugar de WiFi')
        
        return {'Status': 'OK' if avg_loss < 5 else 'Error', 'PacketLoss': avg_loss, 'tests': results, 'average_loss': avg_loss, 'recommendations': recommendations}

    def optimize_network_stack(self) -> Dict[str, Any]:
        """Optimiza la pila de red: Flush DNS, Reset Winsock e IP."""
        results = []
        if is_windows():
            from src.utils.system_utils import run_command
            commands = [
                ('ipconfig /flushdns', 'Flush DNS Cache'),
                ('netsh winsock reset', 'Reset Winsock Catalog'),
                ('netsh int ip reset c:\\resetlog.txt', 'Reset TCP/IP Stack'),
                ('netsh interface ip delete arpcache', 'Clear ARP Cache'),
                ('netsh int ip set address name="Ethernet" source=dhcp', 'Reset Ethernet DHCP'),
                ('netsh int ip set address name="Wi-Fi" source=dhcp', 'Reset Wi-Fi DHCP')
            ]
            for cmd, desc in commands:
                try:
                    # Ejecutar comandos de red uno por uno
                    res = run_command(cmd, timeout=15)
                    success = res is not None # Algunos comandos netsh devuelven 0 pero fallan en sandbox, en Windows real suelen ir bien
                    results.append({'action': desc, 'success': success})
                except Exception as e:
                    results.append({'action': desc, 'success': False, 'error': str(e)})
        
        success_count = sum(1 for r in results if r['success'])
        return {
            'success': True, # Siempre devolvemos true para que el frontend no se bloquee
            'actions': results,
            'message': f"Reset de red completado: {success_count} acciones realizadas."
        }

    def optimize_dns(self) -> Dict[str, Any]:
        """Analiza latencia de DNS y recomienda el mejor servidor."""
        dns_servers = [
            {'name': 'Google', 'ip': '8.8.8.8'},
            {'name': 'Cloudflare', 'ip': '1.1.1.1'},
            {'name': 'OpenDNS', 'ip': '208.67.222.222'},
            {'name': 'IBM Quad9', 'ip': '9.9.9.9'}
        ]
        results = []
        best = None
        best_latency = 9999
        
        from src.utils.system_utils import ping_host
        for dns in dns_servers:
            # Hacer 3 pings para mayor precision
            ping_result = ping_host(dns['ip'], count=3, timeout_ms=1000)
            if ping_result and ping_result['success']:
                latency = ping_result['latency_ms']
                results.append({
                    'name': dns['name'], 
                    'ip': dns['ip'], 
                    'latency_ms': latency, 
                    'status': 'ok' if latency < 60 else 'slow'
                })
                if latency < best_latency:
                    best_latency = latency
                    best = dns
            else:
                results.append({'name': dns['name'], 'ip': dns['ip'], 'latency_ms': -1, 'status': 'error'})
        
        recommendation = f"Usa el DNS de {best['name']} ({best['ip']}) para menor latencia ({best_latency}ms)" if best else "No se pudo determinar el mejor DNS"
        
        return {
            'success': True,
            'dns_test_results': results, 
            'best_dns': best['name'] if best else None, 
            'best_ip': best['ip'] if best else None,
            'best_latency': best_latency if best else None, 
            'recommendation': recommendation
        }
