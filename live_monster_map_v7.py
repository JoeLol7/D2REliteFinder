import ctypes
import struct
import time
import psutil
import matplotlib.pyplot as plt
import math


# ============================================================
# CONFIG
# ============================================================

PROCESS_NAME = "D2R.exe"

PATTERN = bytes.fromhex(
    "48 03 C7 49 8B 8C C6"
)

# Displacement is a signed 32-bit value at pattern + 7
DISP_OFFSET = 7

# UnitHashTable structure
PLAYER_TABLE  = 0x000
NPC_TABLE     = 0x400

BUCKET_COUNT = 128

# UnitAny offsets
OFF_TYPE   = 0x00
OFF_TXT    = 0x04
OFF_ID     = 0x08
OFF_MODE   = 0x0C
OFF_PDATA  = 0x10
OFF_PATH   = 0x38
OFF_STATS  = 0x88

# Path offsets
PATH_Y = 0x02
PATH_X = 0x06

# NPC data
NPC_FLAGS = 0x1A

VIEW_SIZE = 200

UPDATE_TIME = 0.10


# ============================================================
# Windows API
# ============================================================

kernel32 = ctypes.windll.kernel32

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

MEM_COMMIT = 0x1000

PAGE_NOACCESS = 0x01
PAGE_GUARD = 0x100


class MEMORY_BASIC_INFORMATION(ctypes.Structure):

    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_ulong),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
    ]


# ============================================================
# Process
# ============================================================

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


# ============================================================
# Pattern scanner
# ============================================================

PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_WRITECOPY = 0x80

EXECUTABLE_PROTECTIONS = {
    PAGE_EXECUTE_READ,
    PAGE_EXECUTE_READWRITE,
    PAGE_EXECUTE_WRITECOPY,
}


def find_pattern_in_region(handle, base, size, pattern):

    data = read_mem(
        handle,
        base,
        size
    )

    if data is None:
        return []

    results = []

    start = 0

    while True:

        pos = data.find(
            pattern,
            start
        )

        if pos == -1:
            break

        results.append(
            base + pos
        )

        start = pos + 1

    return results


def find_pattern(handle, module_base, module_size, pattern):

    matches = []

    module_end = module_base + module_size

    address = module_base

    mbi = MEMORY_BASIC_INFORMATION()

    while address < module_end:

        result = kernel32.VirtualQueryEx(
            handle,
            ctypes.c_void_p(address),
            ctypes.byref(mbi),
            ctypes.sizeof(mbi)
        )

        if not result:
            break

        region_base = mbi.BaseAddress
        region_size = mbi.RegionSize
        protection = mbi.Protect

        if region_base is None or region_size == 0:
            break

        region_end = region_base + region_size

        # Don't scan outside D2R.exe
        scan_start = max(
            region_base,
            module_base
        )

        scan_end = min(
            region_end,
            module_end
        )

        scan_size = scan_end - scan_start

        if (
            scan_size > 0
            and mbi.State == MEM_COMMIT
            and protection in EXECUTABLE_PROTECTIONS
        ):

            found = find_pattern_in_region(
                handle,
                scan_start,
                scan_size,
                pattern
            )

            matches.extend(found)

        address = region_end

    return matches


# ============================================================
# Find UnitHashTable
# ============================================================

def find_unit_table(handle, module_base, module_size):

    print()
    print("Scanning executable D2R memory for UnitHashTable pattern...")

    matches = find_pattern(
        handle,
        module_base,
        module_size,
        PATTERN
    )

    print(
        f"Pattern matches: {len(matches)}"
    )

    if not matches:

        raise RuntimeError(
            "UnitHashTable pattern not found"
        )

    for match in matches:

        # Pattern:
        #
        # 48 03 C7
        # 49 8B 8C C6
        #             ^^
        #
        # displacement starts at +7

        displacement_address = (
            match + DISP_OFFSET
        )

        data = read_mem(
            handle,
            displacement_address,
            4
        )

        if data is None:
            continue

        displacement = struct.unpack(
            "<i",
            data
        )[0]

        table = (
            module_base
            + displacement
        )

        print()
        print(
            f"Pattern @ 0x{match:X}"
        )

        print(
            f"Displacement = 0x{displacement:X}"
        )

        print(
            f"UnitHashTable = 0x{table:X}"
        )

        # ----------------------------------------------------
        # Validate the table
        # ----------------------------------------------------

        valid_buckets = 0

        for bucket in range(128):

            ptr = u64(
                handle,
                table + bucket * 8
            )

            if (
                ptr is not None
                and ptr > 0x10000000000
            ):
                valid_buckets += 1

        print(
            f"Non-zero player buckets: {valid_buckets}"
        )

        if valid_buckets > 0:

            return table

    raise RuntimeError(
        "Pattern found, but no valid UnitHashTable"
    )


# ============================================================
# UnitAny
# ============================================================

def read_unit(handle, ptr):

    if not ptr:
        return None

    data = read_mem(
        handle,
        ptr,
        0xD0
    )

    if data is None:
        return None

    return {
        "ptr": ptr,

        "type":
            struct.unpack_from("<I", data, OFF_TYPE)[0],

        "txt":
            struct.unpack_from("<I", data, OFF_TXT)[0],

        "id":
            struct.unpack_from("<I", data, OFF_ID)[0],

        "mode":
            struct.unpack_from("<I", data, OFF_MODE)[0],

        "pData":
            struct.unpack_from("<Q", data, OFF_PDATA)[0],

        "pPath":
            struct.unpack_from("<Q", data, OFF_PATH)[0],

        "pStats":
            struct.unpack_from("<Q", data, OFF_STATS)[0],

        "unit_flags":
            struct.unpack_from("<I", data, 0xC8)[0],
    }


# ============================================================
# Position
# ============================================================

def get_position(handle, unit):

    path = unit["pPath"]

    if not path:
        return None

    data = read_mem(
        handle,
        path,
        0x10
    )

    if data is None:
        return None

    y = struct.unpack_from(
        "<H",
        data,
        PATH_Y
    )[0]

    x = struct.unpack_from(
        "<H",
        data,
        PATH_X
    )[0]

    if x == 0 and y == 0:
        return None

    return x, y


# ============================================================
# Player
# ============================================================

def get_player(handle, table):

    for bucket in range(128):

        ptr = u64(
            handle,
            table + bucket * 8
        )

        if not ptr:
            continue

        unit = read_unit(
            handle,
            ptr
        )

        if unit is None:
            continue

        if unit["type"] != 0:
            continue

        pos = get_position(
            handle,
            unit
        )

        if pos is None:
            continue

        unit["x"], unit["y"] = pos

        return unit

    return None


# ============================================================
# Monsters
# ============================================================

def get_monsters(handle, table):

    monsters = []

    npc_table = table + NPC_TABLE

    for bucket in range(128):

        ptr = u64(
            handle,
            npc_table + bucket * 8
        )

        if not ptr:
            continue

        unit = read_unit(
            handle,
            ptr
        )

        if unit is None:
            continue

        if unit["type"] != 1:
            continue

        pos = get_position(
            handle,
            unit
        )

        if pos is None:
            continue

        unit["x"], unit["y"] = pos

        # NPC flags
        flags = 0

        if unit["pData"]:

            value = read_mem(
                handle,
                unit["pData"] + NPC_FLAGS,
                1
            )

            if value is not None:
                flags = value[0]

        unit["flags"] = flags
        unit["rarity"] = get_monster_rarity(flags)

        monsters.append(unit)

    return monsters

def get_monster_rarity(flags):
    if flags & 0x02:
        return "SUPER_UNIQUE"
    elif flags & 0x04:
        return "CHAMPION"
    elif flags & 0x08:
        return "UNIQUE"
    elif flags & 0x10:
        return "MINION"
    else:
        return "NORMAL"

RARITY_STYLE = {
    "NORMAL":       {"marker": "o", "size": 50,  "color": "grey"},
    "MINION":       {"marker": "o", "size": 50,  "color": "gold"},
    "CHAMPION":     {"marker": "D", "size": 100, "color": "blue"},
    "UNIQUE":       {"marker": "*", "size": 150, "color": "gold"},
    "SUPER_UNIQUE": {"marker": "*", "size": 220, "color": "red"},
}

# ============================================================
# Transforms
# ============================================================


def transform_position(x, y):
    # Flip both axes
    x = -x
    y = -y

    # Rotate 45 degrees counter-clockwise
    angle = math.radians(45)

    rx = x * math.cos(angle) - y * math.sin(angle)
    ry = x * math.sin(angle) + y * math.cos(angle)

    return rx, ry

# ============================================================
# Main
# ============================================================

plt.ion()

fig, ax = plt.subplots(
    figsize=(10, 10)
)

fig.canvas.manager.set_window_title(
    "D2R Live Monster Map"
)

player_history = []
MAX_HISTORY = 300

while True:

    try:

        # ----------------------------------------------------
        # Find D2R
        # ----------------------------------------------------

        pid, handle = open_d2r()

        # ----------------------------------------------------
        # Find module
        # ----------------------------------------------------

        base, module_size = get_module_base(pid)

        print(
            f"D2R base: 0x{base:X}"
        )

        print(
            f"Module size: 0x{module_size:X}"
        )

        # ----------------------------------------------------
        # Find UnitHashTable
        # ----------------------------------------------------

        table = find_unit_table(
            handle,
            base,
            module_size
        )

        print()
        print(
            f"Ready. UnitHashTable = 0x{table:X}"
        )
        print()

        # ----------------------------------------------------
        # Live loop
        # ----------------------------------------------------

        while True:

            player = get_player(
                handle,
                table
            )

            monsters = get_monsters(
                handle,
                table
            )

            if player is None:

                time.sleep(
                    UPDATE_TIME
                )

                continue

            # ------------------------------------------------
            # Transform player position
            # ------------------------------------------------

            px, py = transform_position(
                player["x"],
                player["y"]
            )

            player_history.append((px, py))

            if len(player_history) > MAX_HISTORY:
                player_history.pop(0)
                
            hx, hy = zip(*player_history)

            ax.clear()

            # ------------------------------------------------
            # Monsters
            # ------------------------------------------------

            for monster in monsters:
                if monster["rarity"] == "NORMAL":
                    continue
                if monster["mode"] in [0x0C, 0x05, 0x00]:
                    # Skip dead monsters
                    continue

                x, y = transform_position(
                    monster["x"],
                    monster["y"]
                )

                style = RARITY_STYLE[monster["rarity"]]

                ax.scatter(
                    x,
                    y,
                    marker=style["marker"],
                    s=style["size"],
                    color=style["color"],
                    zorder=5
                )

                ax.text(
                    x + 2,
                    y + 2,
                    f'P: {monster["id"]}/{monster["txt"]}\n'
                    f'F: {monster["mode"]:02X}\n',
                    fontsize=7
                )

            # ------------------------------------------------
            # Player
            # ------------------------------------------------

            ax.scatter(
                px,
                py,
                marker="*",
                s=250,
                zorder=10
            )

            ax.plot(
                hx,
                hy,
                linewidth=1,
                alpha=0.5,
                zorder=2
            )

            ax.text(
                px + 3,
                py + 3,
                "YOU",
                fontsize=10,
                fontweight="bold"
            )

            # ------------------------------------------------
            # View
            # ------------------------------------------------

            half = VIEW_SIZE / 2

            ax.set_xlim(
                px - half,
                px + half
            )

            ax.set_ylim(
                py - half,
                py + half
            )

            ax.set_aspect(
                "equal",
                adjustable="box"
            )

            ax.grid(
                True,
                alpha=0.25
            )

            ax.set_xlabel("X")
            ax.set_ylabel("Y")

            ax.set_title(
                f"D2R Live Monster Map    "
                f"Player: {int(px)}, {int(py)}    "
                f"Monsters: {len(monsters)}"
            )

            plt.pause(
                UPDATE_TIME
            )

            # ------------------------------------------------
            # Detect D2R closing
            # ------------------------------------------------

            if find_d2r() != pid:

                print()
                print("D2R closed.")
                print("Waiting for next launch...")

                kernel32.CloseHandle(
                    handle
                )

                break

    except Exception as e:

        print()
        print(
            f"Lost D2R connection: {e}"
        )
        print(
            "Waiting for D2R..."
        )

        try:
            kernel32.CloseHandle(
                handle
            )
        except:
            pass

        time.sleep(1)