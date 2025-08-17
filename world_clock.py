import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QGridLayout, QInputDialog, QGraphicsOpacityEffect
from PySide6.QtCore import QTimer, QTime, Qt, QSize, QPoint, QAbstractAnimation, QPropertyAnimation
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygon, QAction
from PySide6.QtSvgWidgets import QSvgWidget
import pytz
from datetime import datetime
import math
from geopy.geocoders import Nominatim

class DigitalClock(QWidget):
    def __init__(self, timezone_str, parent=None):
        super().__init__(parent)
        self.timezone_str = timezone_str
        self.timezone = pytz.timezone(timezone_str)

        self.layout = QVBoxLayout()
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        font = self.time_label.font()
        font.setPointSize(24)
        self.time_label.setFont(font)

        self.city_label = QLabel(timezone_str.replace('_', ' ').split('/')[-1])
        self.city_label.setAlignment(Qt.AlignCenter)
        font = self.city_label.font()
        font.setPointSize(14)
        self.city_label.setFont(font)

        self.layout.addWidget(self.city_label)
        self.layout.addWidget(self.time_label)
        self.setLayout(self.layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        self.update_time()

    def update_time(self):
        now = datetime.now(self.timezone)
        time_str = now.strftime("%H:%M:%S")
        self.time_label.setText(time_str)

class AnalogClock(QWidget):
    def __init__(self, timezone_str, parent=None):
        super().__init__(parent)
        self.timezone_str = timezone_str
        self.timezone = pytz.timezone(timezone_str)
        self.setMinimumSize(QSize(200, 200))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50) # Update every 50ms for smooth animation

        self.city_label = QLabel(timezone_str.replace('_', ' ').split('/')[-1], self)
        self.city_label.setAlignment(Qt.AlignCenter)
        font = self.city_label.font()
        font.setPointSize(14)
        self.city_label.setFont(font)


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height() - 30) # Adjust for label
        painter.setViewport((self.width() - side) / 2, (self.height() - side - 30) / 2, side, side)
        painter.setWindow(-50, -50, 100, 100)

        # Clock face
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QBrush(Qt.white))
        painter.drawEllipse(-48, -48, 96, 96)

        # Hour markers
        painter.setPen(QPen(Qt.black, 2))
        for i in range(12):
            painter.save()
            painter.rotate(30 * i)
            if (i % 3) == 0:
                painter.drawLine(40, 0, 46, 0)
            else:
                painter.drawLine(42, 0, 46, 0)
            painter.restore()

        now = datetime.now(self.timezone)
        hour = now.hour
        minute = now.minute
        second = now.second
        microsecond = now.microsecond

        # Second hand
        second_angle = (second + microsecond / 1000000.0) * 6.0
        painter.save()
        painter.setPen(QPen(Qt.red, 1))
        painter.rotate(second_angle)
        painter.drawLine(0, 15, 0, -45)
        painter.restore()

        # Minute hand
        minute_angle = (minute + second / 60.0 + microsecond / 60000000.0) * 6.0
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(Qt.darkGray))
        painter.rotate(minute_angle)
        painter.drawPolygon(QPolygon([QPoint(-2, 10), QPoint(2, 10), QPoint(0, -40)]))
        painter.restore()

        # Hour hand
        hour_angle = (hour % 12 + minute / 60.0 + second / 3600.0) * 30.0
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(Qt.black))
        painter.rotate(hour_angle)
        painter.drawPolygon(QPolygon([QPoint(-3, 10), QPoint(3, 10), QPoint(0, -25)]))
        painter.restore()

        # Center circle
        painter.setBrush(QBrush(Qt.red))
        painter.drawEllipse(-2, -2, 4, 4)

        self.city_label.setGeometry(0, self.height() - 30, self.width(), 30)


class MapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(250)

        self.svg_widget = QSvgWidget('assets/world_map.svg', self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.svg_widget)

        self.geolocator = Nominatim(user_agent="world_clock_app")
        self.timezone_locations = {}
        self.coord_cache = {}

        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.update_pulse)
        self.pulse_timer.start(50)
        self.pulse_step = 0

    def update_pulse(self):
        self.pulse_step = (self.pulse_step + 4) % 360
        if self.timezone_locations:
            self.update()

    def update_timezone_locations(self, timezones):
        self.timezone_locations.clear()
        for tz in timezones:
            if tz in self.coord_cache:
                self.timezone_locations[tz] = self.coord_cache[tz]
                continue

            try:
                city = tz.split('/')[-1].replace('_', ' ')
                location = self.geolocator.geocode(city)
                if location:
                    coords = (location.latitude, location.longitude)
                    self.timezone_locations[tz] = coords
                    self.coord_cache[tz] = coords
            except Exception as e:
                print(f"Geocoding error for {tz}: {e}")
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for tz, (lat, lon) in self.timezone_locations.items():
            x = (lon + 180) * self.svg_widget.width() / 360
            y = (90 - lat) * self.svg_widget.height() / 180

            # Pulsing effect
            pulse_radius = 5 + 3 * (1 + math.sin(math.radians(self.pulse_step)))
            pulse_alpha = 100 - 50 * (1 + math.sin(math.radians(self.pulse_step)))
            pulse_color = QColor(255, 0, 0, int(pulse_alpha))
            painter.setBrush(QBrush(pulse_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(int(x), int(y)), int(pulse_radius), int(pulse_radius))

            # Main marker
            painter.setBrush(QBrush(QColor(255, 0, 0, 200)))
            painter.setPen(QPen(QColor(255, 0, 0), 1))
            painter.drawEllipse(QPoint(int(x), int(y)), 5, 5)

    def resizeEvent(self, event):
        self.svg_widget.resize(self.size())
        super().resizeEvent(event)


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

        anim = QPropertyAnimation(opacity_effect, b"opacity")
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
        items = [c.timezone_str for c in self.clocks]
        if not items:
            return
        item, ok = QInputDialog.getItem(self, "Remove Clock", "Select Clock to Remove:", items, 0, False)
        if ok and item:
            self._remove_clock_by_timezone(item)

    def _remove_clock_by_timezone(self, timezone_str):
        clock_to_remove = None
        for clock in self.clocks:
            if clock.timezone_str == timezone_str:
                clock_to_remove = clock
                break

        if clock_to_remove:
            opacity_effect = clock_to_remove.graphicsEffect()
            if not opacity_effect:
                opacity_effect = QGraphicsOpacityEffect(clock_to_remove)
                clock_to_remove.setGraphicsEffect(opacity_effect)

            anim = QPropertyAnimation(opacity_effect, b"opacity")
            anim.setDuration(500)
            anim.setStartValue(1)
            anim.setEndValue(0)
            anim.finished.connect(lambda: self._finalize_clock_removal(clock_to_remove))
            anim.start(QAbstractAnimation.DeleteWhenStopped)

    def _finalize_clock_removal(self, clock_widget):
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

        self.update_map()

    def switch_all_clocks(self, clock_type):
        clocks_to_switch = list(self.clock_positions.values())

        for clock_widget, (row, col) in clocks_to_switch:
            self._remove_clock_by_timezone(clock_widget.timezone_str)
            self.add_clock(clock_widget.timezone_str, clock_type, row=row, col=col)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorldClock()
    window.show()
    sys.exit(app.exec())
