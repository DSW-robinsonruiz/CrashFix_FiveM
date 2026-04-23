# CrashFix FiveM v6.2 PRO

Herramienta web profesional de diagnostico y reparacion automatica disenada para la comunidad de FiveM. Detecta y soluciona de forma inteligente problemas de hardware, software, red y configuracion que causan crasheos en FiveM/GTA V.

---

## Novedades de la Version 6.2 (Abril 2026)

Esta version ha sido sometida a una auditoria tecnica integral, alcanzando un nivel **10/10 en funcionalidad y robustez**.

### Caracteristicas Principales

- **Mantenimiento Total (Un-Solo-Clic):** Sistema de diagnostico inteligente que detecta y aplica automaticamente reparaciones de red, limpieza de cache, desactivacion de mods conflictivos y ajustes de hardware en un solo ciclo.
- **Soporte Multi-GPU Avanzado:** Deteccion precisa de sistemas hibridos (laptops Intel/NVIDIA). Identifica VRAM real y prioriza la GPU dedicada para diagnosticos termicos y de rendimiento.
- **Monitoreo Proactivo 24/7:** Vigilancia en tiempo real. Emite alertas visuales instantaneas si detecta temperaturas criticas, falta de RAM o perdida de paquetes mientras esta abierta.
- **Base de Datos de Errores 2024-2026:** Actualizada con los patrones de error mas recientes de FiveM, incluyendo `ERR_GFX_D3D_SWAPCHAIN_ALLOC`, `Pool Size Overflow` y crasheos de memoria en `GTA5.exe+`.
- **Robustez Anti-Windows:** Logica de fuerza bruta para el borrado de archivos. Maneja automaticamente permisos de escritura y reintentos para eliminar carpetas bloqueadas de cache y logs sin fallar.
- **Validacion Real de Drivers GPU:** La actualizacion de drivers NVIDIA y AMD verifica la version instalada antes y despues del proceso. Solo marca exito si el cambio fue real, eliminando falsos positivos.
- **Escritura Real en CitizenFX.ini:** La configuracion de Texture Budget escribe directamente en el archivo de configuracion de FiveM y verifica el resultado post-escritura.

---

## Funcionalidades Detalladas

### Diagnostico Exhaustivo

| Area | Descripcion |
|---|---|
| **Hardware** | Analisis de GPU, RAM, CPU y almacenamiento con deteccion de temperaturas en tiempo real |
| **Software** | Identificacion de overlays conflictivos (Discord, Steam, NVIDIA) y programas en segundo plano (MSI Afterburner, RivaTuner) |
| **Red** | Test de latencia, perdida de paquetes (Packet Loss) y optimizador de DNS segun ubicacion |
| **Integridad** | Verificacion de archivos esenciales de GTA V y versiones de VC++ Redistributables |

### Reparaciones y Optimizaciones

| Funcion | Descripcion |
|---|---|
| **Limpieza Inteligente** | Borrado selectivo o completo de cache y logs de FiveM con gestion de permisos |
| **Reparacion de ROS** | Solucion de problemas de autenticacion de Rockstar Online Services |
| **Ajustes Graficos** | Calculador de Texture Budget basado en VRAM y optimizacion automatica de `settings.xml` |
| **Configuracion de CitizenFX.ini** | Escritura directa del Texture Budget en el archivo de configuracion con verificacion post-escritura |
| **Actualizacion de Drivers** | Descarga e instalacion de drivers NVIDIA/AMD con validacion real de version pre y post instalacion |
| **Windows Gaming** | Configuracion de reglas de Firewall, exclusiones de Defender y optimizacion de la pila de red (TCP/IP Reset) |

### Reparaciones Avanzadas Disponibles

| ID | Reparacion |
|---|---|
| 1 | Terminar procesos de FiveM |
| 2 | Limpiar cache selectiva |
| 3 | Limpiar cache completa |
| 4 | Eliminar DLLs conflictivas |
| 5 | Limpiar v8 DLLs (System32) |
| 6 | Limpiar archivos ROS |
| 7 | Reparar autenticacion ROS |
| 8 | Desactivar mods de GTA V |
| 9 | Cerrar software conflictivo |
| 10 | Configurar reglas de Firewall |
| 11 | Optimizar configuracion grafica |
| 12 | Configurar Texture Budget |
| 13 | Optimizaciones de Windows |
| 14 | Actualizar driver GPU |
| 15 | Limpiar logs de FiveM |

---

## Instalacion y Uso

### Requisitos

| Requisito | Detalle |
|---|---|
| **Python** | 3.11 o superior |
| **Sistema Operativo** | Windows 10/11 (funcionalidad completa) |
| **Permisos** | Administrador (necesarios para reparaciones de sistema y actualizacion de drivers) |
| **Dependencias** | Flask >= 2.3.0 |

### Guia Rapida

```bash
# 1. Clonar el repositorio
git clone https://github.com/ROCLIC/CrashFix_FiveM.git
cd CrashFix_FiveM/CrashFix_FiveM

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar la aplicacion
python app.py
```

Accede a la interfaz desde tu navegador en: `http://127.0.0.1:5000`

---

## Estructura del Proyecto

```
CrashFix_FiveM/
├── app.py                          # Servidor Flask principal y API
├── config.py                       # Configuracion centralizada y base de datos de errores
├── requirements.txt                # Dependencias del proyecto
├── src/
│   ├── services/
│   │   ├── diagnostic_service.py   # Logica de diagnostico integral
│   │   ├── hardware_service.py     # Deteccion de GPU, RAM, CPU, temperaturas
│   │   ├── network_service.py      # Tests de red, latencia y DNS
│   │   ├── repair_service.py       # Reparaciones, optimizaciones y actualizacion de drivers
│   │   └── session_manager.py      # Gestion de sesiones y reportes
│   └── utils/
│       ├── file_utils.py           # Operaciones seguras de archivos y backups
│       ├── logging_utils.py        # Configuracion de logging
│       ├── system_utils.py         # Wrappers de comandos del sistema (PowerShell, procesos)
│       └── validation.py           # Validacion de datos de entrada
├── static/
│   ├── css/style.css               # Estilos de la interfaz
│   └── js/app.js                   # Logica del frontend
└── templates/
    └── index.html                  # Interfaz principal
```

---

## Licencia

Este proyecto esta bajo la Licencia Apache 2.0. Consulta el archivo [LICENSE](LICENSE) para mas detalles.

---

Desarrollado para mejorar la estabilidad de la comunidad de FiveM.
