"""
Monitoraggio risorse hardware (CPU, RAM, OS tramite WMI e Win32 API)
e verifica delle porte locali tramite libreria `socket`.
"""

import time
import socket
import ctypes
import wmi


def get_system_metrics(include_wmi_cpu=True):
    """
    Recupera l'utilizzo di CPU e RAM (riattivando in modo sicuro le metriche WMI
    presenti nel codice originale di main.py).
    """
    cpu_usage = 0.0
    total_memory_mb = 0.0
    free_memory_mb = 0.0
    ram_usage = 0.0
    os_caption = "Windows"

    # Lettura immediata RAM tramite Win32 API
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        mem = MEMORYSTATUSEX()
        mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
        total_memory_mb = mem.ullTotalPhys / (1024 * 1024)
        free_memory_mb = mem.ullAvailPhys / (1024 * 1024)
        ram_usage = round(total_memory_mb - free_memory_mb, 2)
    except Exception:
        pass

    # Query WMI (Win32_Processor & Win32_OperatingSystem)
    if include_wmi_cpu:
        w = None
        processors = None
        operating_system = None
        try:
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass
            w = wmi.WMI()
            processors = w.Win32_Processor()
            if processors and processors[0].LoadPercentage is not None:
                cpu_usage = float(processors[0].LoadPercentage)
            operating_system = w.Win32_OperatingSystem()[0]
            os_caption = getattr(operating_system, "Caption", "Windows").strip()
            total_memory_mb = int(operating_system.TotalVisibleMemorySize) / 1024
            free_memory_mb = int(operating_system.FreePhysicalMemory) / 1024
            ram_usage = round(total_memory_mb - free_memory_mb, 2)
        except Exception:
            pass
        finally:
            operating_system = None
            processors = None
            w = None
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass

    return {
        "cpu_usage": cpu_usage,
        "total_memory_mb": round(total_memory_mb, 2),
        "free_memory_mb": round(free_memory_mb, 2),
        "ram_usage": ram_usage,
        "os_caption": os_caption
    }


def check_local_port(host, port, timeout=0.35):
    """
    Verifica tramite libreria `socket` se una porta TCP locale (es. 127.0.0.1:80, 443, 3306)
    è aperta e in ascolto, restituendo (is_open, latency_ms, detail_message).
    """
    t0 = time.perf_counter()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, int(port)))
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        if result == 0:
            return True, elapsed_ms, f"Connessione riuscita su {host}:{port}"
        return False, elapsed_ms, f"Porta chiusa / nessun listener (codice {result})"
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        return False, elapsed_ms, f"Errore socket: {exc}"
    finally:
        try:
            sock.close()
        except Exception:
            pass
