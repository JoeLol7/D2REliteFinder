import psutil


from memory.units import (
    get_item_position,
    get_item_quality,
    read_unit,
    get_position,
    get_monster_rarity,
    get_object_type
)

from memory.process import read_mem

from memory.object_data import load_object_data

from config import (
    PLAYER_TABLE,
    NPC_TABLE,
    BUCKET_COUNT,
    NPC_FLAGS,
    OBJECT_TABLE,
    ITEM_TABLE
)


class D2RGame:

    def __init__(self, handle, table, pid):

        self.handle = handle
        self.table = table
        self.pid = pid
        self.object_data = load_object_data()

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

            stats = unit["pStats"]

            if not stats:
                return None

            stat_array = self._read_pointer(stats + 0x30)
            count = self._read_uint16(stats + 0x38)

            if not stat_array or count is None:
                return None

            for i in range(count):

                stat_ptr = stat_array + i * 8

                code = self._read_uint16(stat_ptr + 0x02)
                value = self._read_uint32(stat_ptr + 0x04)

                if code == 0x0D:
                    unit["xp"] = value

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

            while ptr:
                
                next_ptr = self._read_pointer(ptr + 0x158)
                
                unit = read_unit(
                    self.handle,
                    ptr
                )

                if unit is None:
                    ptr = next_ptr
                    continue

                # Monster/NPC unit type
                if unit["type"] != 1:
                    ptr = next_ptr
                    continue

                position = get_position(
                    self.handle,
                    unit
                )

                if position is None:
                    ptr = next_ptr
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
                
                ptr = next_ptr

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

            txt = unit["txt"]

            obj_data = self.object_data.get(txt)

            if obj_data:
                unit["name"] = obj_data["name"]
                unit["class"] = obj_data["class"]
                unit["subclass"] = obj_data["subclass"]
                unit["operate_fn"] = obj_data["operate_fn"]
                unit["populate_fn"] = obj_data["populate_fn"]
                unit["init_fn"] = obj_data["init_fn"]
            else:
                unit["name"] = ""
                unit["class"] = ""
                unit["subclass"] = ""
                unit["operate_fn"] = ""
                unit["populate_fn"] = ""
                unit["init_fn"] = ""

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

            objects.append(unit)

        return objects

    def get_items(self):
        items = []
        item_table = self.table + ITEM_TABLE

        for bucket in range(BUCKET_COUNT):
            ptr = self._read_pointer(
                item_table + bucket * 8
            )
            
            if not ptr:
                continue
                    
            while ptr:

                unit = read_unit(
                    self.handle,
                    ptr
                )

                if unit is None:
                    break

                next_ptr = self._read_pointer(ptr + 0x158)

                if unit["mode"] not in [3,5]:
                    ptr = next_ptr
                    continue

                if unit["type"] != 4:
                    ptr = next_ptr
                    continue

                path = unit["pPath"]

                if not path:
                    ptr = next_ptr
                    continue

                position = get_item_position(
                    self.handle,
                    unit
                )

                if position is None:
                    ptr = next_ptr
                    continue

                unit["x"], unit["y"] = position
                unit["quality"] = get_item_quality(
                    self.handle,
                    unit
                )

                #print(
                #    f"Item: id={unit['id']} mode={unit['mode']} txt={unit['txt']} pos=({unit['x']}, {unit['y']}) quality={unit['quality']}"
                #)

                items.append(unit)

                next_ptr = self._read_pointer(ptr + 0x158)

                ptr = next_ptr
        #print(f"Found {len(items)} items.")
        return items

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

    def _read_uint16(self, address):

        data = self._read(
            address,
            2
        )

        if data is None:
            return None

        return int.from_bytes(
            data,
            byteorder="little"
        )


    def _read_uint32(self, address):

        data = self._read(
            address,
            4
        )

        if data is None:
            return None

        return int.from_bytes(
            data,
            byteorder="little"
        )