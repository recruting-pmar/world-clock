from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import QTimer, Qt, QSize, QPoint, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygon
import pytz
from datetime import datetime
import math

class DigitalClock(QWidget):
    hover_event = Signal(str, bool) # timezone, is_entering

    def __init__(self, timezone_str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_Hover, True)
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

    def hoverEnterEvent(self, event):
        self.hover_event.emit(self.timezone_str, True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.hover_event.emit(self.timezone_str, False)
        super().hoverLeaveEvent(event)

class AnalogClock(QWidget):
    hover_event = Signal(str, bool) # timezone, is_entering

    def __init__(self, timezone_str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_Hover, True)
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
        # Color Palette
        face_color = QColor("#3C3C3C")
        marker_color = QColor("#CCCCCC")
        hour_minute_hand_color = QColor("#CCCCCC")
        second_hand_color = QColor("#00BFFF") # DeepSkyBlue

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height() - 30) # Adjust for label
        painter.setViewport((self.width() - side) / 2, (self.height() - side - 30) / 2, side, side)
        painter.setWindow(-50, -50, 100, 100)

        # Clock face
        painter.setPen(QPen(marker_color, 2))
        painter.setBrush(QBrush(face_color))
        painter.drawEllipse(-48, -48, 96, 96)

        # Hour markers
        painter.setPen(QPen(marker_color, 2))
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
        painter.setPen(QPen(second_hand_color, 1))
        painter.rotate(second_angle)
        painter.drawLine(0, 15, 0, -45)
        painter.restore()

        # Minute hand
        minute_angle = (minute + second / 60.0 + microsecond / 60000000.0) * 6.0
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(hour_minute_hand_color))
        painter.rotate(minute_angle)
        painter.drawPolygon(QPolygon([QPoint(-2, 10), QPoint(2, 10), QPoint(0, -40)]))
        painter.restore()

        # Hour hand
        hour_angle = (hour % 12 + minute / 60.0 + second / 3600.0) * 30.0
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(hour_minute_hand_color))
        painter.rotate(hour_angle)
        painter.drawPolygon(QPolygon([QPoint(-3, 10), QPoint(3, 10), QPoint(0, -25)]))
        painter.restore()

        # Center circle
        painter.setBrush(QBrush(second_hand_color))
        painter.drawEllipse(-2, -2, 4, 4)

        self.city_label.setGeometry(0, self.height() - 30, self.width(), 30)

    def hoverEnterEvent(self, event):
        self.hover_event.emit(self.timezone_str, True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.hover_event.emit(self.timezone_str, False)
        super().hoverLeaveEvent(event)
