from pathlib import Path


OBJECTS_FILE = Path(__file__).parent.parent / "data" / "objects.txt"


def load_object_data():
    objects = {}

    with open(OBJECTS_FILE, "r", encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")

        for line in f:
            values = line.rstrip("\n").split("\t")

            if len(values) != len(header):
                continue

            obj = dict(zip(header, values))

            try:
                obj_id = int(obj["*ID"])
            except (ValueError, KeyError):
                continue

            objects[obj_id] = {
                "name": obj.get("Name", ""),
                "class": obj.get("Class", ""),
                "subclass": int(obj.get("SubClass", "")),
                "operate_fn": int(obj.get("OperateFn", "")),
                "populate_fn": int(obj.get("PopulateFn", "")),
                "init_fn": int(obj.get("InitFn", "")),
            }

    return objects