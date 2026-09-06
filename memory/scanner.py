
# ============================================================
# Pattern scanner
# ============================================================

from memory.process import read_mem, u64, MEM_COMMIT
from config import PATTERN, DISP_OFFSET
from memory.structs import MEMORY_BASIC_INFORMATION
import ctypes
import struct

PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_WRITECOPY = 0x80

EXECUTABLE_PROTECTIONS = {
    PAGE_EXECUTE_READ,
    PAGE_EXECUTE_READWRITE,
    PAGE_EXECUTE_WRITECOPY,
}

kernel32 = ctypes.windll.kernel32

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