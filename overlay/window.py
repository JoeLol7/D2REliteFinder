import ctypes
import math

from ctypes import wintypes

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget


user32 = ctypes.windll.user32


# ==========================================================
# Coordinate transform
# ==========================================================

def transform_position(x, y):

    # Flip both axes
    x = -x
    y = -y

    # Rotate 45 degrees counter-clockwise
    angle = math.radians(45)

    rx = x * math.cos(angle) - y * math.sin(angle)
    ry = x * math.sin(angle) + y * math.cos(angle)

    return rx, ry


# ==========================================================
# Overlay
# ==========================================================

class OverlayWindow(QWidget):

    def __init__(self, pid):

        super().__init__()

        self.pid = pid

        self.player = None
        self.monsters = []
        self.objects = []

        self.history = []

        self.view_size = 200
        self.map_size = 1000

        self.scale_x = 6.6
        self.scale_y = 3.35

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        self.setAttribute(
            Qt.WA_TranslucentBackground
        )

        self.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True
        )

        self.hide()

    def make_click_through(self):

        hwnd = int(self.winId())

        GWL_EXSTYLE = -20

        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020

        style = user32.GetWindowLongW(
            hwnd,
            GWL_EXSTYLE
        )

        style |= WS_EX_LAYERED
        style |= WS_EX_TRANSPARENT

        user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            style
        )

    # ======================================================
    # Find D2R window
    # ======================================================

    def find_d2r_window(self):

        hwnd_result = None

        @ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HWND,
            wintypes.LPARAM
        )
        def enum_callback(hwnd, lparam):

            nonlocal hwnd_result

            process_id = wintypes.DWORD()

            user32.GetWindowThreadProcessId(
                hwnd,
                ctypes.byref(process_id)
            )

            if process_id.value != self.pid:
                return True

            if not user32.IsWindowVisible(hwnd):
                return True

            hwnd_result = hwnd

            return False

        user32.EnumWindows(
            enum_callback,
            0
        )

        return hwnd_result

    # ======================================================
    # Follow D2R window
    # ======================================================

    def update_position(self):

        hwnd = self.find_d2r_window()

        if not hwnd:

            self.hide()

            return

        rect = wintypes.RECT()

        if not user32.GetWindowRect(
            hwnd,
            ctypes.byref(rect)
        ):
            return

        left = rect.left
        top = rect.top

        width = rect.right - rect.left
        height = rect.bottom - rect.top

        self.setGeometry(
            left,
            top,
            width,
            height
        )

        if not self.isVisible():

            self.show()

            self.make_click_through()

        self.raise_()

    # ======================================================
    # Set game state
    # ======================================================

    def set_state(
        self,
        player,
        monsters,
        history,
        objects
    ):

        self.player = player
        self.monsters = monsters
        self.history = history
        self.objects = objects

        self.update()

    # ======================================================
    # World -> overlay coordinates
    # ======================================================

    def world_to_overlay(
        self,
        x,
        y,
        player_x,
        player_y
    ):

        # Transform world position
        wx, wy = transform_position(x, y)

        # Transform player position
        px, py = transform_position(
            player_x,
            player_y
        )

        # Position relative to player
        dx = wx - px
        dy = wy - py

        # Scale
        scale = self.map_size / self.view_size


        map_cx = self.width() / 2
        map_cy = self.height() / 2 - 10

        # Qt Y axis is inverted compared with our map
        return (
            map_cx + dx * self.scale_x,
            map_cy - dy * self.scale_y
        )

    # ======================================================
    # Draw
    # ======================================================

    def paintEvent(self, event):

        if self.player is None:

            return

        painter = QPainter(self)

        try:

            painter.setRenderHint(
                QPainter.Antialiasing
            )

            player_x = self.player["x"]
            player_y = self.player["y"]

            # --------------------------------------------------
            # Minimap size / position
            # --------------------------------------------------


            map_cx = self.width() / 2
            map_cy = self.height() / 2 - 10

            map_left = map_cx - self.map_size / 2
            map_top = map_cy - self.map_size / 2

            # --------------------------------------------------
            # Semi-transparent background
            # --------------------------------------------------

            painter.setPen(
                Qt.NoPen
            )

            painter.setBrush(
                QBrush(
                    Qt.black,
                    Qt.SolidPattern
                )
            )

            # Don't make the whole thing opaque
            painter.setOpacity(0.25)

            #painter.drawRoundedRect(
            #    map_left,
            #    map_top,
            #    self.map_size,
            #    self.map_size,
            #    10,
            #    10
            #)

            painter.setOpacity(0.5)

            # --------------------------------------------------
            # Draw player trail
            # --------------------------------------------------

            if len(self.history) > 1:

                pen = QPen(Qt.white)

                pen.setWidth(2)

                painter.setPen(pen)

                previous = None

                for hx, hy in self.history:

                    sx, sy = self.world_to_overlay(
                        hx,
                        hy,
                        player_x,
                        player_y
                    )

                    if previous is not None:
                        if abs(sx - previous[0]) < 100 and abs(sy - previous[1]) < 100:
                            painter.drawLine(
                                int(previous[0]),
                                int(previous[1]),
                                int(sx),
                                int(sy)
                            )

                    previous = (
                        sx,
                        sy
                    )

            painter.setOpacity(1.0)

            # --------------------------------------------------
            # Draw monsters
            # --------------------------------------------------

            for monster in self.monsters:

                x = monster["x"]
                y = monster["y"]

                sx, sy = self.world_to_overlay(
                    x,
                    y,
                    player_x,
                    player_y
                )

                # Ignore monsters outside minimap
                if not (
                    map_left <= sx <= map_left + self.map_size
                    and
                    map_top <= sy <= map_top + self.map_size
                ):
                    continue

                rarity = monster["rarity"]

                if rarity == "NORMAL":

                    marker = "o"
                    size = 100
                    color = Qt.white

                elif rarity == "MINION":

                    marker = "o"
                    size = 100
                    color = Qt.yellow

                elif rarity == "CHAMPION":

                    marker = "o"
                    size = 100
                    color = Qt.blue

                elif rarity == "UNIQUE":

                    marker = "*"
                    size = 200
                    color = Qt.yellow

                elif rarity == "SUPER_UNIQUE":

                    marker = "*"
                    size = 300
                    color = Qt.red

                else:

                    continue

                font = QFont()

                font.setPointSize(
                    max(8, int(size / 10))
                )

                font.setBold(True)

                painter.setFont(font)

                painter.setPen(
                    QPen(color)
                )

                painter.drawText(
                    int(sx - 6),
                    int(sy + 6),
                    marker
                )

            # --------------------------------------------------
            # Objects
            # --------------------------------------------------

            for obj in self.objects:

                type = obj["type"]

                if type == "SUPER_CHEST":
                    marker = "SC"
                    color = Qt.green
                elif type == "CHEST":
                    marker = "C"
                    color = Qt.red
                elif type == "GEM_SHRINE":
                    marker = "GS"
                    color = Qt.cyan
                elif type == "WEAPON_RACK":
                    marker = "W"
                    color = Qt.cyan
                elif type == "ARMOUR_STAND":
                    marker = "A"
                    color = Qt.cyan
                else:
                    marker = ""#f"O:{obj['txt']}"
                    color = Qt.white
                
                sx, sy = self.world_to_overlay(
                    obj["x"],
                    obj["y"],
                    self.player["x"],
                    self.player["y"]
                )

                painter.setPen(
                    QPen(color)
                )

                font.setPointSize(
                    max(8, int(100 / 10))
                )

                painter.drawText(
                    int(sx - 5),
                    int(sy + 5),
                    marker
                )

            # --------------------------------------------------
            # Player
            # --------------------------i------------------------

            painter.setPen(
                QPen(Qt.white)
            )

            painter.setBrush(
                QBrush(Qt.white)
            )

            painter.drawEllipse(
                int(map_cx - 5),
                int(map_cy - 5),
                10,
                10
            )

            # --------------------------------------------------
            # Border
            # --------------------------------------------------

            painter.setBrush(
                Qt.NoBrush
            )

            painter.setPen(
                QPen(Qt.white, 1)
            )

            #painter.drawRoundedRect(
            #    map_left,
            #    map_top,
            #    self.map_size,
            #    self.map_size,
            #    10,
            #    10
            #)

        except Exception as e:

            print(f"Error in paintEvent: {e}")
            painter.end()