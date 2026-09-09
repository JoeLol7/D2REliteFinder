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
ITEM_TABLE = 0x1000

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

ITEM_Y = 0x10
ITEM_X = 0x14

# ============================================================
# ITEM DATA
# ============================================================

ITEM_DATA_SIZE = 0x56

ITEM_DATA_QUALITY = 0x00

# ============================================================
# NPC
# ============================================================

NPC_FLAGS = 0x1A

# ============================================================
# OVERLAY / DISPLAY
# ============================================================

VIEW_SIZE = 200

UPDATE_TIME = 0.05

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

SUPER_CHEST_IDS = {
    387,
    389,
    390,
    391,
    455,
    580,
    581
}

RUNES = {
    645: "PUL",
    646: "UM",
    647: "MAL",
    648: "IST",
    649: "GUL",
    650: "VEX",
    651: "OHM",
    652: "LO",
    653: "SUR",
    654: "BER",
    655: "JAH",
    656: "CHAM",
    657: "ZOD",
}