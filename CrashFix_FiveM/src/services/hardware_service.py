# -*- coding: utf-8 -*-
import json
import logging
import os
import time
from typing import Dict, List, Any, Optional
from src.utils.system_utils import is_windows, run_powershell, run_command

logger = logging.getLogger(__name__)

class HardwareService:
    def __init__(self, config):
        self.config = config
        self.timeout_config = config.timeout_config

    def get_gpu_info(self) -> List[Dict[str, Any]]:
        """Detecta informacion de GPU con VRAM precisa."""
        gpus = []
        if is_windows():
            nvidia_vram = self._get_nvidia_vram()
            try:
                result = run_powershell(
                    'Get-WmiObject Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion, PNPDeviceID | ConvertTo-Json',
                    timeout=self.timeout_config.powershell_timeout
                )
                if result:
                    data = json.loads(result)
                    if not isinstance(data, list): data = [data]
                    for gpu in data:
                        name = gpu.get('Name', 'Desconocido')
                        driver = gpu.get('DriverVersion', 'N/A')
                        pnp_id = gpu.get('PNPDeviceID', '')
                        vram_gb = 0
                        if nvidia_vram and 'nvidia' in name.lower():
                            vram_gb = nvidia_vram
                        else:
                            reg_vram = self._get_vram_from_registry(pnp_id)
                            if reg_vram > 0: vram_gb = reg_vram
                        if vram_gb == 0:
                            adapter_ram = gpu.get('AdapterRAM', 0)
                            if adapter_ram and int(adapter_ram) > 0:
                                vram_gb = round(int(adapter_ram) / (1024**3), 1)
                        gpus.append({'Name': name, 'VRAM_GB': vram_gb, 'DriverVersion': driver})
            except: pass
        if not gpus: gpus = [{'Name': 'No detectada', 'VRAM_GB': 0, 'DriverVersion': 'N/A'}]
        return gpus

    def _get_nvidia_vram(self) -> float:
        try:
            result = run_command(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'], timeout=self.timeout_config.nvidia_smi_timeout)
            if result and result.returncode == 0:
                vram_mb = int(result.stdout.strip().split('\n')[0])
                return round(vram_mb / 1024, 1)
        except: pass
        return 0

    def _get_vram_from_registry(self, pnp_device_id: str) -> float:
        if not pnp_device_id: return 0
        try:
            result = run_powershell(
                'Get-ItemProperty -Path "HKLM:\\SYSTEM\\ControlSet001\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}\\0*" '
                '-Name HardwareInformation.qwMemorySize -ErrorAction SilentlyContinue | '
                'Select-Object -ExpandProperty "HardwareInformation.qwMemorySize" | Select-Object -First 1',
                timeout=self.timeout_config.powershell_timeout
            )
            if result:
                vram_bytes = int(result.strip())
                if vram_bytes > 0: return round(vram_bytes / (1024**3), 1)
        except: pass
        return 0

    def get_ram_info(self) -> Dict[str, Any]:
        ram_info = {'TotalGB': 0, 'AvailableGB': 0, 'UsedPercent': 0}
        if is_windows():
            try:
                result = run_powershell('Get-WmiObject Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory | ConvertTo-Json', timeout=self.timeout_config.powershell_timeout)
                if result:
                    data = json.loads(result)
                    total_kb = int(data.get('TotalVisibleMemorySize', 0))
                    free_kb = int(data.get('FreePhysicalMemory', 0))
                    if total_kb > 0:
                        ram_info = {'TotalGB': round(total_kb / (1024**2), 1), 'AvailableGB': round(free_kb / (1024**2), 1), 'UsedPercent': round((1 - free_kb/total_kb) * 100, 1)}
            except: pass
        return ram_info

    def get_cpu_info(self) -> Dict[str, Any]:
        cpu_info = {'Name': 'Desconocido', 'Cores': 0, 'Threads': 0, 'MaxSpeed': 0}
        if is_windows():
            try:
                result = run_powershell('Get-WmiObject Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed | ConvertTo-Json', timeout=self.timeout_config.powershell_timeout)
                if result:
                    data = json.loads(result)
                    if isinstance(data, list): data = data[0]
                    cpu_info = {'Name': data.get('Name', 'Desconocido'), 'Cores': data.get('NumberOfCores', 0), 'Threads': data.get('NumberOfLogicalProcessors', 0), 'MaxSpeed': data.get('MaxClockSpeed', 0)}
            except: pass
        return cpu_info

    def profile_pc_tier(self) -> str:
        """Clasifica el PC en gama baja, media o alta."""
        ram = self.get_ram_info().get('TotalGB', 0)
        gpu = self.get_gpu_info()[0].get('VRAM_GB', 0)
        cpu_cores = self.get_cpu_info().get('Cores', 0)
        
        if ram >= 16 and gpu >= 8 and cpu_cores >= 8:
            return 'high'
        elif ram >= 8 and gpu >= 4 and cpu_cores >= 4:
            return 'medium'
        else:
            return 'low'

    def get_temperatures(self) -> Dict[str, Any]:
        """Monitoreo de temperaturas de CPU y GPU."""
        temps = {'cpu': None, 'gpu': None, 'status': 'unknown'}
        if is_windows():
            try:
                # Intento de obtener temperatura de GPU via nvidia-smi
                result = run_command(['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader'], timeout=self.timeout_config.nvidia_smi_timeout)
                if result and result.returncode == 0:
                    temps['gpu'] = int(result.stdout.strip())
                
                # Intento de obtener temperatura de CPU via WMI (puede requerir privilegios de admin)
                cpu_res = run_powershell('Get-WmiObject -Namespace "root\\WMI" -Class MSAcpi_ThermalZoneTemperature | Select-Object CurrentTemperature | ConvertTo-Json')
                if cpu_res:
                    data = json.loads(cpu_res)
                    if isinstance(data, list): data = data[0]
                    # El valor es en décimas de Kelvin
                    temps['cpu'] = round((data.get('CurrentTemperature', 0) / 10) - 273.15, 1)
            except: pass
            
        if temps['cpu'] and temps['cpu'] > 85 or temps['gpu'] and temps['gpu'] > 85:
            temps['status'] = 'overheating'
        elif temps['cpu'] or temps['gpu']:
            temps['status'] = 'normal'
            
        return temps

    def run_benchmark(self) -> Dict[str, Any]:
        results = {'cpu_score': 0, 'memory_score': 0, 'disk_score': 0, 'overall_score': 0, 'rating': 'Desconocido', 'fivem_ready': False}
        cpu_info = self.get_cpu_info()
        results['cpu_score'] = min(100, (cpu_info.get('Cores', 2) * 10) + (cpu_info.get('Threads', 4) * 5))
        ram_info = self.get_ram_info()
        results['memory_score'] = min(100, int(ram_info.get('TotalGB', 8) * 6))
        results['overall_score'] = round((results['cpu_score'] * 0.5) + (results['memory_score'] * 0.5))
        results['rating'] = 'Excelente' if results['overall_score'] >= 80 else 'Bueno' if results['overall_score'] >= 60 else 'Regular'
        results['fivem_ready'] = results['overall_score'] >= 50
        return results
