from pathlib import Path


OBJECTS_FILE = Path(__file__).parent.parent / "data" / "objects.txt"


def load_objects():
    with open(OBJECTS_FILE, "r", encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")

        objects = []

        for line in f:
            values = line.rstrip("\n").split("\t")

            if len(values) != len(header):
                continue

            obj = dict(zip(header, values))

            try:
                obj_id = int(obj["*ID"])
            except (ValueError, KeyError):
                continue

            obj["id"] = obj_id
            objects.append(obj)

    return objects


def main():
    objects = load_objects()

    print()
    print("CHEST OBJECTS")
    print("=" * 100)

    for obj in objects:
        object_class = obj.get("Class", "").lower()
        name = obj.get("Name", "").lower()
        description = obj.get("*Description", "").lower()

        # Start broad — anything that looks like a chest
        if (
            "chest" in object_class
            or "chest" in name
            or "chest" in description
        ):
            print(
                f'{obj["id"]:4} | '
                f'{obj.get("Class", ""):20} | '
                f'{obj.get("Name", ""):30} | '
                f'SubClass={obj.get("SubClass", ""):3} | '
                f'OperateFn={obj.get("OperateFn", ""):3} | '
                f'PopulateFn={obj.get("PopulateFn", ""):3} | '
                f'InitFn={obj.get("InitFn", "")}'
            )


if __name__ == "__main__":
    main()