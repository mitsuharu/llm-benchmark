"""Best-effort local host metadata. Unknown values remain null."""
import csv
import os
import platform
import subprocess

def query(*args):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL, timeout=10).strip()
    except (OSError, subprocess.SubprocessError):
        return None

def detect():
    system = platform.system()
    cpu = platform.processor() or None
    ram = None
    if system == "Linux":
        try:
            with open("/proc/meminfo") as f:
                ram = int(next(line for line in f if line.startswith("MemTotal:")).split()[1]) * 1024
            with open("/proc/cpuinfo") as f:
                cpu = next((line.split(":", 1)[1].strip() for line in f if line.startswith("model name")), cpu)
        except (OSError, ValueError, StopIteration):
            pass
    elif system == "Darwin":
        cpu = query("sysctl", "-n", "machdep.cpu.brand_string") or cpu
        value = query("sysctl", "-n", "hw.memsize")
        ram = int(value) if value and value.isdigit() else None
    elif system == "Windows":
        value = query("powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory")
        ram = int(value) if value and value.isdigit() else None
        cpu = query("powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name") or cpu
    gpus = []
    output = query("nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits")
    if output:
        for row in csv.reader(output.splitlines()):
            if len(row) == 3:
                name, memory, driver = (x.strip() for x in row)
                gpus.append(dict(name=name, vram_bytes=int(memory)*1024**2 if memory.isdigit() else None, driver=driver, source="nvidia-smi"))
    return dict(os=system, release=platform.release(), architecture=platform.machine(), cpu=cpu,
                logical_cpus=os.cpu_count(), ram_bytes=ram, detected_nvidia_gpus=gpus or None)
