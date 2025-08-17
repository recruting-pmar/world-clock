import sys
import pytz
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QGridLayout, QInputDialog, QGraphicsOpacityEffect)
from PySide6.QtCore import QAbstractAnimation, QPropertyAnimation
from PySide6.QtGui import QAction

from widgets import AnalogClock, DigitalClock, MapWidget

class WorldClock(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("World Clock")
        self.setGeometry(100, 100, 800, 800)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        clocks_container = QWidget()
        self.grid_layout = QGridLayout(clocks_container)

        self.map_widget = MapWidget()

        main_layout.addWidget(clocks_container)
        main_layout.addWidget(self.map_widget)
        main_layout.setStretch(0, 3) # Clocks take 3/4 of space
        main_layout.setStretch(1, 1) # Map takes 1/4 of space

        self.clocks = []
        self.clock_positions = {} # To store widget and its position

        self._create_menu()

        # Add some default clocks
        self.add_clock("Europe/London")
        self.add_clock("Asia/Tokyo", clock_type="digital")
        self.add_clock("Australia/Sydney", clock_type="digital")
        self.add_clock("America/Los_Angeles")

        self.update_map()

    def _create_menu(self):
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")

        add_clock_action = QAction("Add Clock...", self)
        add_clock_action.triggered.connect(self.prompt_add_clock)
        file_menu.addAction(add_clock_action)

        remove_clock_action = QAction("Remove Clock...", self)
        remove_clock_action.triggered.connect(self.prompt_remove_clock)
        file_menu.addAction(remove_clock_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menu_bar.addMenu("View")

        self.analog_action = QAction("Switch to Analog", self)
        self.analog_action.triggered.connect(lambda: self.switch_all_clocks("analog"))
        view_menu.addAction(self.analog_action)

        self.digital_action = QAction("Switch to Digital", self)
        self.digital_action.triggered.connect(lambda: self.switch_all_clocks("digital"))
        view_menu.addAction(self.digital_action)

    def find_next_available_slot(self):
        # Find the next available slot in a 4x2 grid
        for i in range(8):
            row, col = i % 2, i // 2
            is_occupied = False
            for pos_widget, (pos_row, pos_col) in self.clock_positions.values():
                if row == pos_row and col == pos_col:
                    is_occupied = True
                    break
            if not is_occupied:
                return row, col
        return None, None

    def update_map(self):
        timezones = [c.timezone_str for c in self.clocks]
        self.map_widget.update_timezone_locations(timezones)

    def add_clock(self, timezone, clock_type="analog", row=None, col=None):
        if len(self.clocks) >= 8 and (row is None or col is None):
            print("Maximum number of clocks reached.")
            return

        if row is None or col is None:
            row, col = self.find_next_available_slot()
            if row is None:
                print("No available slots.")
                return

        if clock_type == "analog":
            clock_widget = AnalogClock(timezone)
        else:
            clock_widget = DigitalClock(timezone)

        opacity_effect = QGraphicsOpacityEffect(clock_widget)
        clock_widget.setGraphicsEffect(opacity_effect)

        self.grid_layout.addWidget(clock_widget, row, col)
        self.clocks.append(clock_widget)
        self.clock_positions[id(clock_widget)] = (clock_widget, (row, col))
        self.update_map()

        anim = QPropertyAnimation(opacity_effect, b"opacity", parent=opacity_effect)
        anim.setDuration(500)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start(QAbstractAnimation.DeleteWhenStopped)

    def prompt_add_clock(self):
        if len(self.clocks) >= 8:
            print("Maximum number of clocks reached.")
            return
        timezone, ok = QInputDialog.getItem(self, "Add Clock", "Select Timezone:", pytz.common_timezones, 0, False)
        if ok and timezone:
            self.add_clock(timezone)

    def prompt_remove_clock(self):
        # Create a list of unique descriptions for the user to select from
        items = [f"{i+1}: {c.timezone_str}" for i, c in enumerate(self.clocks)]
        if not items:
            return

        item, ok = QInputDialog.getItem(self, "Remove Clock", "Select Clock to Remove:", items, 0, False)
        if ok and item:
            # Extract the index from the selected string
            index_to_remove = int(item.split(':')[0]) - 1
            clock_to_remove = self.clocks[index_to_remove]
            self._remove_clock_widget(clock_to_remove, on_finished=self.update_map)

    def _remove_clock_widget(self, clock_widget, on_finished=None):
        if clock_widget:
            opacity_effect = clock_widget.graphicsEffect()
            if not opacity_effect:
                opacity_effect = QGraphicsOpacityEffect(clock_widget)
                clock_widget.setGraphicsEffect(opacity_effect)

            anim = QPropertyAnimation(opacity_effect, b"opacity", parent=opacity_effect)
            anim.setDuration(500)
            anim.setStartValue(1)
            anim.setEndValue(0)

            anim.finished.connect(lambda: self._finalize_clock_removal(clock_widget, on_finished))
            anim.start(QAbstractAnimation.DeleteWhenStopped)

    def _finalize_clock_removal(self, clock_widget, on_finished_callback=None):
        self.grid_layout.removeWidget(clock_widget)
        clock_widget.deleteLater()
        if clock_widget in self.clocks:
            self.clocks.remove(clock_widget)

        clock_id_to_remove = None
        for cid, (cw, _) in self.clock_positions.items():
            if cw is clock_widget:
                clock_id_to_remove = cid
                break
        if clock_id_to_remove:
            del self.clock_positions[clock_id_to_remove]

        if on_finished_callback:
            on_finished_callback()

    def switch_all_clocks(self, clock_type):
        # Create a static list of clocks to switch, as the instance list will be modified
        clocks_to_switch = list(self.clocks)

        for clock_widget in clocks_to_switch:
            # Find the position of the clock to be switched
            clock_id_to_find = None
            for cid, (cw, pos) in self.clock_positions.items():
                if cw is clock_widget:
                    clock_id_to_find = cid
                    break

            if clock_id_to_find:
                _, (row, col) = self.clock_positions[clock_id_to_find]
                timezone = clock_widget.timezone_str

                # Define what to do after the clock is removed
                add_new_clock_callback = lambda tz=timezone, r=row, c=col, ct=clock_type: self.add_clock(tz, ct, r, c)
                # Remove the old clock, and when it's done, add the new one
                self._remove_clock_widget(clock_widget, on_finished=add_new_clock_callback)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorldClock()
    window.show()
    sys.exit(app.exec())
