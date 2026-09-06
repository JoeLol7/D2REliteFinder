

# ============================================================
# Process
# ============================================================

import psutil
import ctypes
import time
import struct
from config import PROCESS_NAME

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

MEM_COMMIT = 0x1000

kernel32 = ctypes.windll.kernel32


def find_d2r():

    for proc in psutil.process_iter(["pid", "name"]):

        try:
            name = proc.info["name"]

            if name and name.lower() == PROCESS_NAME.lower():
                return proc.info["pid"]

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return None


def open_d2r():

    while True:

        pid = find_d2r()

        if pid is not None:

            handle = kernel32.OpenProcess(
                PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
                False,
                pid
            )

            if handle:

                print()
                print("=" * 70)
                print("D2R FOUND")
                print("=" * 70)
                print(f"PID: {pid}")

                return pid, handle

        print("Waiting for D2R.exe...")

        time.sleep(1)


# ============================================================
# Module information
# ============================================================

def get_module_base(pid):

    # psutil gives us the mapped executable path.
    proc = psutil.Process(pid)

    exe_path = proc.exe()

    # Use Windows Toolhelp snapshot to find the module base.
    TH32CS_SNAPMODULE = 0x00000008
    TH32CS_SNAPMODULE32 = 0x00000010

    class MODULEENTRY32(ctypes.Structure):

        _fields_ = [
            ("dwSize", ctypes.c_ulong),
            ("th32ModuleID", ctypes.c_ulong),
            ("th32ProcessID", ctypes.c_ulong),
            ("GlblcntUsage", ctypes.c_ulong),
            ("ProccntUsage", ctypes.c_ulong),
            ("modBaseAddr", ctypes.POINTER(ctypes.c_ubyte)),
            ("modBaseSize", ctypes.c_ulong),
            ("hModule", ctypes.c_void_p),
            ("szModule", ctypes.c_char * 256),
            ("szExePath", ctypes.c_char * 260),
        ]

    snapshot = kernel32.CreateToolhelp32Snapshot(
        TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32,
        pid
    )

    if snapshot == ctypes.c_void_p(-1).value:
        raise RuntimeError("CreateToolhelp32Snapshot failed")

    entry = MODULEENTRY32()
    entry.dwSize = ctypes.sizeof(MODULEENTRY32)

    if not kernel32.Module32First(snapshot, ctypes.byref(entry)):

        kernel32.CloseHandle(snapshot)

        raise RuntimeError("Module32First failed")

    base = None

    while True:

        module_name = entry.szModule.decode(
            errors="ignore"
        )

        if module_name.lower() == PROCESS_NAME.lower():

            base = ctypes.addressof(entry.modBaseAddr.contents)

            break

        if not kernel32.Module32Next(
            snapshot,
            ctypes.byref(entry)
        ):
            break

    kernel32.CloseHandle(snapshot)

    if base is None:
        raise RuntimeError("Could not find D2R module")

    return base, entry.modBaseSize


# ============================================================
# Memory
# ============================================================

def read_mem(handle, address, size):

    buffer = ctypes.create_string_buffer(size)

    bytes_read = ctypes.c_size_t()

    ok = kernel32.ReadProcessMemory(
        handle,
        ctypes.c_void_p(address),
        buffer,
        size,
        ctypes.byref(bytes_read)
    )

    if not ok or bytes_read.value != size:
        return None

    return buffer.raw


def u32(handle, address):

    data = read_mem(handle, address, 4)

    if data is None:
        return None

    return struct.unpack("<I", data)[0]


def u64(handle, address):

    data = read_mem(handle, address, 8)

    if data is None:
        return None

    return struct.unpack("<Q", data)[0]