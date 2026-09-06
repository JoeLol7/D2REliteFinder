# D2R Map Overlay

A lightweight real-time map overlay for **Diablo II: Resurrected**.

The project reads game state directly from the running D2R process and displays a transparent, click-through overlay over the game window. It currently tracks the player and monsters, with additional work underway to identify chests, containers, and other interactive objects.

> **⚠️ Early development / experimental**
>
> This project is primarily a reverse-engineering and learning project. Memory structures and offsets may change between D2R versions.

## Features

### Live map overlay

* Automatically locates the running D2R window.
* Follows the game window when moved or resized.
* Transparent, borderless overlay.
* Click-through so it doesn't interfere with normal gameplay.
* Real-time player position.
* Player movement history / trail.
* Monster positions.
* Monster rarity detection.
* Dead monster filtering.
* Configurable map scaling and aspect ratio.

### Monster detection

Monsters are currently read from D2R's `UnitHashTable`.

The project identifies:

* Normal monsters
* Minions
* Champions
* Uniques
* Super Uniques

Normal monsters can be filtered out so that the overlay focuses on more interesting targets.

Monster rarity is currently determined from NPC data flags.

### Object detection

The project can also enumerate D2R objects from the object section of the unit table.

Objects currently expose:

* Unit ID
* `txtFileNo`
* Mode
* World X/Y position

The overlay can display temporary object markers such as:

```text
O:397
O:403
O:346
```

This is currently being used to identify chests, super chests, barrels, crates and other interactable objects.

## Project structure

```text
D2RMap/
├── main.py
├── config.py
│
├── memory/
│   ├── __init__.py
│   ├── process.py
│   ├── scanner.py
│   ├── units.py
│   └── game.py
│
└── overlay/
    ├── __init__.py
    └── window.py
```

### `main.py`

Application entry point.

Responsible for:

* Connecting to D2R
* Finding the `UnitHashTable`
* Creating the game interface
* Starting the Qt event loop
* Updating the overlay

### `config.py`

Contains user-configurable settings such as:

* D2R process name
* Update interval
* Map view size
* Movement history length
* Monster marker styles
* Coordinate scaling

### `memory/process.py`

Handles Windows process interaction:

* Finding D2R
* Opening the process
* Reading process memory
* Finding the D2R module base
* Windows memory APIs

### `memory/scanner.py`

Contains runtime pattern scanning used to locate important D2R structures.

This avoids relying entirely on hard-coded absolute addresses and allows the program to work with ASLR.

### `memory/units.py`

Contains the low-level representation of D2R units.

Currently handles:

* Reading `UnitAny`
* Reading unit type
* Reading `txtFileNo`
* Reading unit ID
* Reading mode
* Reading `pData`
* Reading `pPath`
* Reading world coordinates
* Monster rarity flags

### `memory/game.py`

Higher-level interface to the current game state.

Provides methods such as:

```python
get_player()
get_monsters()
get_objects()
```

### `overlay/window.py`

PySide6 overlay implementation.

Responsible for:

* Tracking the D2R window
* Rendering the map
* Rendering the player
* Rendering monsters
* Rendering movement history
* Rendering objects
* Coordinate transformation
* Click-through behaviour

## D2R memory structures

The project currently locates the `UnitHashTable` dynamically using a signature/pattern scan.

The table is structured into five sections:

```text
UnitHashTable
│
├── +0x000  Players
├── +0x400  NPCs / Monsters
├── +0x800  Objects
├── +0xC00  Missiles
└── +0x1000 Items
```

Each section contains 128 entries.

The current project has verified that unit IDs correspond to their hash bucket using:

```python
unit_id % 128
```

For example:

```text
Unit ID 926
926 % 128 = 30
```

and the unit appears in bucket 30.

### UnitAny

The currently verified fields used by the project include:

| Offset | Field       |
| -----: | ----------- |
| `0x00` | Type        |
| `0x04` | `txtFileNo` |
| `0x08` | Unit ID     |
| `0x0C` | Mode        |
| `0x10` | `pData`     |
| `0x38` | `pPath`     |
| `0x88` | `pStats`    |

These offsets are based on runtime testing against the D2R version currently being developed against and should not be assumed to remain valid forever.

## Coordinates

Player and monster coordinates are read from their path structure.

Object coordinates use the static coordinate fields instead:

```text
pPath + 0x10 → X
pPath + 0x14 → Y
```

The different coordinate representation was discovered while testing object enumeration.

## Monster death state

The project currently uses the unit's `mode` to filter dead monsters.

Observed states include:

```text
0x01  Normal / inactive
0x02  Aggro
0x03  Hit / animation
0x05  Death animation
0x00  Death animation / transition
0x0C  Fully dead
```

The overlay currently excludes:

```python
[0x0C, 0x05, 0x00]
```

## Coordinate transformation

D2R's world coordinates are transformed for the map display.

The current transformation:

1. Flips X and Y.
2. Rotates the coordinate system by 45°.
3. Converts the resulting world position into overlay coordinates.

This produces a map orientation that matches the in-game map more closely.

The overlay also supports independent horizontal and vertical scaling to compensate for the game's isometric projection.

## Monster rarity

NPC data contains flags which currently allow the project to distinguish several monster types.

Current interpretation:

```text
0x02 → Super Unique
0x04 → Champion
0x08 → Unique
0x10 → Minion
```

Normal monsters have none of these flags.

The interpretation is based on runtime testing and should be treated as experimental until fully verified against D2R's current data structures.

## Object detection

Objects are read from:

```text
UnitHashTable + 0x800
```

Objects have:

```text
type == 2
```

The project's object debugging mode displays the object's `txtFileNo`.

For example:

```text
OBJECT id=3133 txt=346 mode=0 x=12663 y=9351
OBJECT id=3134 txt=403 mode=0 x=12690 y=9358
OBJECT id=3151 txt=397 mode=0 x=12640 y=9379
```

The goal is to build a useful classification of objects such as:

* Chests
* Super chests
* Sparkly chests
* Barrels
* Crates
* Corpses
* Weapon racks
* Armor racks
* Other interactable objects

Rather than maintaining a huge hard-coded list, the project will investigate D2R's object data and runtime properties to determine whether objects can be classified generically.

## Requirements

* Windows
* Diablo II: Resurrected
* Python 3.x
* PySide6
* psutil

Install the Python dependencies with:

```bash
pip install PySide6 psutil
```

## Running

Start Diablo II: Resurrected first, then run:

```bash
python main.py
```

The application will:

1. Locate the D2R process.
2. Open the process for memory reading.
3. Locate the D2R module.
4. Pattern-scan for the `UnitHashTable`.
5. Start the overlay.
6. Continuously update the player, monsters and objects.

## Configuration

Most user-facing settings are kept in:

```text
config.py
```

For example:

```python
PROCESS_NAME = "D2R.exe"

UPDATE_TIME = 0.10

MAX_HISTORY = 300

VIEW_SIZE = 100
```

Monster marker appearance can also be configured there.

## Why pattern scanning?

D2R uses ASLR, meaning the module can load at a different address each time the game starts.

Instead of relying on an absolute address such as:

```text
0x7FF75EC90000
```

the project searches the live process memory for a known instruction pattern and calculates the required address from the result.

This makes the project considerably less dependent on a particular D2R process address.

## Version

Development is currently being performed against:

```text
Diablo II: Resurrected
Version 3.3.93847
```

Memory layouts can change with game updates. If D2R is updated, the pattern signatures and/or structure offsets may need to be re-verified.

## Disclaimer

This project is intended for **offline / single-player experimentation, reverse engineering and educational purposes**.

It is not intended for use on Battle.net or for gaining an unfair advantage in online play.

Use at your own risk.

## Credits & references

This project has benefited from publicly available D2R reverse-engineering work and documentation, particularly work documenting:

* D2R memory structures
* Unit tables
* Runtime pattern scanning
* Unit paths and coordinates
* D2R game data tables

Relevant projects and references include:

* D2RLegit / MapAssist
* D2R MapView
* ChrisTitusTech / diablo2utils
* Blizzard data extracted into community-maintained D2R data tables

## Roadmap

* [x] Locate D2R process
* [x] Locate module base
* [x] Pattern-scan `UnitHashTable`
* [x] Read player
* [x] Read monsters
* [x] Read monster positions
* [x] Detect monster rarity
* [x] Filter dead monsters
* [x] Render transparent overlay
* [x] Track D2R window
* [x] Render player position
* [x] Render movement history
* [x] Enumerate objects
* [x] Read object coordinates
* [ ] Identify chest object IDs
* [ ] Identify super chests
* [ ] Identify other useful interactable objects
* [ ] Automatically classify objects
* [ ] Add configurable object markers
* [ ] Improve unit enumeration
* [ ] Add items
* [ ] Improve map rendering
* [ ] Handle D2R updates more robustly

---

**This is very much a work in progress.**

The project started as an exercise in understanding D2R's runtime memory structures and has gradually turned into a lightweight live map/overlay.
