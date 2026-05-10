import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QFont

# -------------------- STYLES --------------------
CARD_STYLE = """
QFrame{
    background:#0f172a;
    border:1px solid #1e293b;
    border-radius:18px;
}
QLabel{color:white;}
"""

BADGE_STYLE = """
QLabel{
    background:#16a34a;
    color:white;
    padding:6px 14px;
    border-radius:14px;
    font-weight:bold;
}
"""

# -------------------- COMPONENTS --------------------
class Card(QFrame):
    def __init__(self, title, value="", color="#22c55e"):
        super().__init__()
        self.setStyleSheet(CARD_STYLE)

        layout = QVBoxLayout(self)

        t = QLabel(title)
        t.setStyleSheet("color:#94a3b8;font-size:13px;")

        v = QLabel(value)
        v.setStyleSheet(f"color:{color};font-size:26px;font-weight:bold;")

        layout.addWidget(t)
        layout.addWidget(v)
        layout.addStretch()


class FocusCircle(QFrame):
    def __init__(self, value="85/100"):
        super().__init__()
        self.setStyleSheet("background:#0f172a;border-radius:120px;border:2px solid #22c55e;")
        self.setFixedSize(180, 180)

        layout = QVBoxLayout(self)

        label = QLabel(value)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size:28px;color:#22c55e;font-weight:bold;")

        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()


# -------------------- MAIN UI --------------------
class SafeDriveUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SafeDriveVision")
        self.resize(1600, 900)
        self.setStyleSheet("background:#020617;")

        main = QVBoxLayout(self)

        # -------- TOP BAR --------
        top = QHBoxLayout()

        title = QLabel("SafeDriveVision")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setStyleSheet("color:#22c55e;")

        self.status = QLabel("ACTIVE")
        self.status.setStyleSheet(BADGE_STYLE)

        self.clock = QLabel()
        self.clock.setStyleSheet("color:#38bdf8;font-size:14px;")

        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.status)
        top.addSpacing(20)
        top.addWidget(self.clock)

        main.addLayout(top)

        # clock update
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)

        # -------- BODY --------
        body = QHBoxLayout()

        # LEFT CAMERA PANEL
        left = QVBoxLayout()

        self.camera = QFrame()
        self.camera.setMinimumSize(900, 650)
        self.camera.setStyleSheet("""
            background:#020617;
            border:2px solid #22c55e;
            border-radius:20px;
        """)

        overlay = QLabel("AI CAMERA ACTIVE", self.camera)
        overlay.move(30, 20)
        overlay.setStyleSheet("color:#22c55e;font-size:18px;font-weight:bold;")

        left.addWidget(self.camera)

        # BOTTOM ALERT CHIPS
        chips = QHBoxLayout()

        for txt in ["EYES", "YAWN", "PHONE", "LOOK AWAY"]:
            chip = QLabel(txt)
            chip.setStyleSheet("""
                background:#111827;
                border:1px solid #334155;
                padding:8px 16px;
                border-radius:16px;
                color:white;
            """)
            chips.addWidget(chip)

        left.addLayout(chips)

        # RIGHT PANEL
        right = QGridLayout()

        right.addWidget(FocusCircle("92"), 0, 0, 1, 2)

        right.addWidget(Card("STATUS", "SAFE"), 1, 0)
        right.addWidget(Card("YAWNS", "2", "#facc15"), 1, 1)
        right.addWidget(Card("LOOK AWAY", "3", "#f97316"), 2, 0)
        right.addWidget(Card("PHONE", "0", "#38bdf8"), 2, 1)

        # RECENT ALERTS
        alerts = Card("RECENT ALERTS", "Look Away\nYawn\nLook Away", "#ef4444")
        right.addWidget(alerts, 3, 0, 1, 2)

        body.addLayout(left, 3)
        body.addLayout(right, 1)

        main.addLayout(body)

    def update_time(self):
        current = QTime.currentTime().toString("hh:mm:ss")
        self.clock.setText(current)


# -------------------- RUN --------------------
app = QApplication(sys.argv)
window = SafeDriveUI()
window.show()
sys.exit(app.exec())
