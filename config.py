# ============================================================
# PROCESS
# ============================================================

PROCESS_NAME = "D2R.exe"

# ============================================================
# UNIT HASH TABLE
# ============================================================

PATTERN = bytes.fromhex(
    "48 03 C7 49 8B 8C C6"
)

# Displacement is a signed 32-bit value at pattern + 7
DISP_OFFSET = 7

# UnitHashTable structure
PLAYER_TABLE  = 0x000
NPC_TABLE     = 0x400
OBJECT_TABLE = 0x800

BUCKET_COUNT = 128

# ============================================================
# UNITANY
# ============================================================

OFF_TYPE   = 0x00
OFF_TXT    = 0x04
OFF_ID     = 0x08
OFF_MODE   = 0x0C
OFF_PDATA  = 0x10
OFF_PATH   = 0x38
OFF_STATS  = 0x88

# ============================================================
# PATH
# ============================================================

PATH_Y = 0x02
PATH_X = 0x06

# ============================================================
# NPC
# ============================================================

NPC_FLAGS = 0x1A

# ============================================================
# OVERLAY / DISPLAY
# ============================================================

VIEW_SIZE = 200

UPDATE_TIME = 0.10

MAX_HISTORY = 300

# ============================================================
# MONSTER DISPLAY
# ============================================================

RARITY_STYLE = {
    "NORMAL":       {"marker": "o", "size": 50,  "color": "grey"},
    "MINION":       {"marker": "o", "size": 50,  "color": "gold"},
    "CHAMPION":     {"marker": "D", "size": 100, "color": "blue"},
    "UNIQUE":       {"marker": "*", "size": 150, "color": "gold"},
    "SUPER_UNIQUE": {"marker": "*", "size": 220, "color": "red"},
}

# ============================================================
# Windows API
# ============================================================

RARITY_STYLE = {
    "NORMAL":       {"marker": "o", "size": 50,  "color": "grey"},
    "MINION":       {"marker": "o", "size": 50,  "color": "gold"},
    "CHAMPION":     {"marker": "D", "size": 100, "color": "blue"},
    "UNIQUE":       {"marker": "*", "size": 150, "color": "gold"},
    "SUPER_UNIQUE": {"marker": "*", "size": 220, "color": "red"},
}
