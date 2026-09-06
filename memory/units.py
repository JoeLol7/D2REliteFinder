

from memory.process import read_mem
import struct
from config import OFF_TYPE, OFF_TXT, OFF_ID, OFF_MODE, OFF_PDATA, OFF_PATH, OFF_STATS, PATH_Y, PATH_X, NPC_FLAGS, NPC_TABLE

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

def get_object_type(txt):
    if txt in [181,183,397, 406]:
        return "SUPER_CHEST"
    elif txt in [126,433,501,502,504,510]:
        return "CHEST"
    elif txt in [124, 495]:
        return "SHRINE"
    elif txt in [107]:
        return "WEAPON_RACK"
    elif txt in [104]:
        return "ARMOUR_STAND"
    else:
        return "UNKNOWN"
