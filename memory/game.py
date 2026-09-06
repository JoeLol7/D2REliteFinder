import psutil


from memory.units import (
    read_unit,
    get_position,
    get_monster_rarity,
    get_object_type
)

from memory.process import read_mem

from config import (
    PLAYER_TABLE,
    NPC_TABLE,
    BUCKET_COUNT,
    NPC_FLAGS,
    OBJECT_TABLE,
)


class D2RGame:

    def __init__(self, handle, table, pid):

        self.handle = handle
        self.table = table
        self.pid = pid

    # ========================================================
    # Process
    # ========================================================

    def is_running(self):

        try:

            process = psutil.Process(self.pid)

            return process.is_running()

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied
        ):

            return False

    # ========================================================
    # Player
    # ========================================================

    def get_player(self):

        for bucket in range(BUCKET_COUNT):

            ptr = self._read_pointer(
                self.table + PLAYER_TABLE + bucket * 8
            )

            if not ptr:
                continue

            unit = read_unit(
                self.handle,
                ptr
            )

            if unit is None:
                continue

            # Player unit type
            if unit["type"] != 0:
                continue

            position = get_position(
                self.handle,
                unit
            )

            if position is None:
                continue

            unit["x"], unit["y"] = position

            return unit

        return None

    # ========================================================
    # Monsters
    # ========================================================

    def get_monsters(self):

        monsters = []

        npc_table = (
            self.table + NPC_TABLE
        )

        for bucket in range(BUCKET_COUNT):

            ptr = self._read_pointer(
                npc_table + bucket * 8
            )


            if not ptr:
                continue

            unit = read_unit(
                self.handle,
                ptr
            )

            #print(
            #    f"bucket={bucket:3d} "
            #    f"ptr=0x{ptr:X} "
            #    f"id={unit['id']} "
            #    f"txt={unit['txt']} "
            #    f"mode={unit['mode']}"
            #)
            
            next_ptr = self._read_pointer(ptr + 0x150)

            if next_ptr:
                print(
                    f"*** NEXT POINTER: bucket={bucket} "
                    f"id={unit['id']} "
                    f"next=0x{next_ptr:X}"
                )

            if unit is None:
                continue

            # Monster/NPC unit type
            if unit["type"] != 1:
                continue

            position = get_position(
                self.handle,
                unit
            )

            if position is None:
                continue

            unit["x"], unit["y"] = position

            # ------------------------------------------------
            # NPC flags / rarity
            # ------------------------------------------------

            flags = 0

            if unit["pData"]:

                data = self._read(
                    unit["pData"] + NPC_FLAGS,
                    1
                )

                if data is not None:

                    flags = data[0]

            unit["flags"] = flags

            unit["rarity"] = get_monster_rarity(
                flags
            )

            monsters.append(unit)

        return monsters

    def get_objects(self):
        objects = []
        object_table = self.table + OBJECT_TABLE

        for bucket in range(BUCKET_COUNT):
            ptr = self._read_pointer(
                object_table + bucket * 8
            )

            if not ptr:
                continue

            unit = read_unit(
                self.handle,
                ptr
            )

            if unit is None:
                continue

            if unit["type"] != 2:
                continue

            path = unit["pPath"]

            if not path:
                continue

            data = self._read(
                path + 0x10,
                6
            )

            if data is None:
                continue

            y = int.from_bytes(data[0:2], "little")
            x = int.from_bytes(data[4:6], "little")

            position = x, y
            unit["x"] = x
            unit["y"] = y

            if position is None:
                continue

            unit["x"], unit["y"] = position

            unit["type"] = get_object_type(
                unit["txt"]
            )

            objects.append(unit)

        return objects

    # ========================================================
    # Memory helpers
    # ========================================================

    def _read(self, address, size):

        return read_mem(
            self.handle,
            address,
            size
        )

    def _read_pointer(self, address):

        data = self._read(
            address,
            8
        )

        if data is None:
            return None

        return int.from_bytes(
            data,
            byteorder="little"
        )