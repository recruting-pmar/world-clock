import math
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import QTimer, QPoint, Qt
from PySide6.QtGui import QPainter, QBrush, QColor, QPen
from PySide6.QtSvgWidgets import QSvgWidget
from geopy.geocoders import Nominatim

class MapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(250)

        self.svg_widget = QSvgWidget('assets/world_map.svg', self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.svg_widget)

        self.geolocator = Nominatim(user_agent="world_clock_app", timeout=10)
        self.timezone_locations = {}
        self.coord_cache = {}
        self.highlighted_timezone = None

        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.update_pulse)
        self.pulse_timer.start(50)
        self.pulse_step = 0

    def update_pulse(self):
        self.pulse_step = (self.pulse_step + 4) % 360
        if self.timezone_locations:
            self.update()

    def set_highlighted_timezone(self, timezone):
        if self.highlighted_timezone != timezone:
            self.highlighted_timezone = timezone
            self.update()

    def update_timezone_locations(self, timezones):
        self.timezone_locations.clear()
        for tz in timezones:
            if tz in self.coord_cache:
                self.timezone_locations[tz] = self.coord_cache[tz]
                continue

            try:
                # Extract city name from timezone
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

            marker_color = QColor("#00BFFF")

            # Highlight effect
            if tz == self.highlighted_timezone:
                highlight_color = QColor("#FFD700") # Gold
                highlight_color.setAlpha(150)
                painter.setBrush(QBrush(highlight_color))
                painter.setPen(QPen(highlight_color.darker(150), 2))
                painter.drawEllipse(QPoint(int(x), int(y)), 12, 12)

            # Pulsing effect
            pulse_radius = 5 + 3 * (1 + math.sin(math.radians(self.pulse_step)))
            pulse_alpha = 100 - 50 * (1 + math.sin(math.radians(self.pulse_step)))

            pulse_color = QColor(marker_color)
            pulse_color.setAlpha(int(pulse_alpha))

            painter.setBrush(QBrush(pulse_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(int(x), int(y)), int(pulse_radius), int(pulse_radius))

            # Main marker
            main_marker_color = QColor(marker_color)
            main_marker_color.setAlpha(200)
            painter.setBrush(QBrush(main_marker_color))
            painter.setPen(QPen(marker_color, 1))
            painter.drawEllipse(QPoint(int(x), int(y)), 5, 5)

    def resizeEvent(self, event):
        self.svg_widget.resize(self.size())
        super().resizeEvent(event)
