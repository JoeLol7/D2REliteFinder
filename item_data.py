from pathlib import Path
import csv


DATA_DIR = Path(__file__).parent / "data"


_unique_items = {}
_set_items = {}


def load_item_file(filename):
    path = DATA_DIR / filename

    if not path.exists():
        print(f"Item data file not found: {path}")
        return {}

    items = {}

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(
            f,
            delimiter="\t"
        )

        for row in reader:

            item_id = row.get("*ID", "").strip()
            name = row.get("index", "").strip()

            if not item_id or not name:
                continue

            try:
                item_id = int(item_id)
            except ValueError:
                continue

            items[item_id] = name

    print(
        f"Loaded {len(items)} items from {filename}"
    )

    return items


def initialise_item_data():

    global _unique_items
    global _set_items

    _unique_items = load_item_file(
        "UniqueItems.txt"
    )

    _set_items = load_item_file(
        "SetItems.txt"
    )


def get_item_name(item):

    quality = item.get("quality")
    item_id = item.get("unique_or_set_id")

    if item_id is None:
        return None

    try:
        item_id = int(item_id)
    except (TypeError, ValueError):
        return None

    if quality == 7:
        return _unique_items.get(item_id)

    if quality == 5:
        return _set_items.get(item_id)

    return None