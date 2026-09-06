import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from config import UPDATE_TIME

from memory.process import get_module_base, open_d2r
from memory.scanner import find_unit_table
from memory.game import D2RGame

from overlay.window import OverlayWindow


def main():

    print("Connecting to D2R...")

    pid, handle = open_d2r()

    if handle is None:
        print("Could not connect to D2R.")
        return

    print(f"D2R PID: {pid}")

    base, module_size = get_module_base(pid)

    table = find_unit_table(handle, base, module_size)

    if table is None:
        print("Could not find UnitTable.")
        return

    print(f"UnitTable: 0x{table:X}")

    # --------------------------------------------------
    # Game reader
    # --------------------------------------------------

    game = D2RGame(
        handle,
        table,
        pid
    )

    # --------------------------------------------------
    # Qt application
    # --------------------------------------------------

    app = QApplication(sys.argv)

    overlay = OverlayWindow(pid)

    # --------------------------------------------------
    # Player history
    # --------------------------------------------------

    history = []

    # --------------------------------------------------
    # Update function
    # --------------------------------------------------

    def update():

        if not game.is_running():

            print("D2R closed.")

            app.quit()
            return

        # Keep overlay aligned with D2R
        overlay.update_position()

        # --------------------------------------------------
        # Player
        # --------------------------------------------------

        player = game.get_player()

        if player is None:
            return

        x = player["x"]
        y = player["y"]

        # --------------------------------------------------
        # Player history
        # --------------------------------------------------

        history.append((x, y))

        if len(history) > 300:
            history.pop(0)

        # --------------------------------------------------
        # Monsters
        # --------------------------------------------------

        monsters = game.get_monsters()
        objects = game.get_objects()

        visible_monsters = []

        for monster in monsters:

            # Ignore normal monsters
            #if monster["rarity"] == "NORMAL":
            #    continue

            # Ignore dead/death animation states
            if monster["mode"] in [0x0C, 0x05, 0x00]:
                continue

            visible_monsters.append(monster)

        # --------------------------------------------------
        # Send state to overlay
        # --------------------------------------------------

        overlay.set_state(
            player,
            visible_monsters,
            history,
            objects
        )

    # --------------------------------------------------
    # Timer
    # --------------------------------------------------

    timer = QTimer()

    timer.timeout.connect(update)

    timer.start(
        int(UPDATE_TIME * 1000)
    )

    # Do one update immediately
    update()

    # --------------------------------------------------
    # Run Qt
    # --------------------------------------------------

    exit_code = app.exec()

    handle.close()

    sys.exit(exit_code)


if __name__ == "__main__":

    while True:
        main()

        try:
            main()

        except Exception as e:

            print(f"Error: {e}")
            print("Restarting...")