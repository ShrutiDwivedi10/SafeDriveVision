import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QFrame,
    QVBoxLayout, QHBoxLayout, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QFont


CARD = """
QFrame{
    background:#08111f;
    border:1px solid #10243f;
    border-radius:22px;
}
"""

PILL = """
QLabel{
    background:#0a1728;
    border-radius:16px;
    padding:10px 20px;
    color:#22c55e;
    font-size:18px;
    font-weight:bold;
}
"""


class Card(QFrame):
    def __init__(self, title, value="", color="white"):
        super().__init__()
        self.setStyleSheet(CARD)

        lay = QVBoxLayout(self)

        t = QLabel(title)
        t.setStyleSheet("color:#cbd5e1;font-size:18px;font-weight:bold;")
        lay.addWidget(t)

        self.v = QLabel(value)
        self.v.setStyleSheet(
            f"color:{color};font-size:34px;font-weight:bold;"
        )
        lay.addWidget(self.v)

        lay.addStretch()


class SafeDriveProUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SafeDrive Vision Pro")
        self.resize(1600, 900)
        self.setStyleSheet("background:#030712;")

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(18)

        # ---------- TOP ----------
        top = QHBoxLayout()

        left_title = QVBoxLayout()

        title = QLabel("SafeDrive Vision")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setStyleSheet("color:white;")

        sub = QLabel("AI Driver Monitoring System")
        sub.setStyleSheet("color:#94a3b8;font-size:15px;")

        left_title.addWidget(title)
        left_title.addWidget(sub)

        top.addLayout(left_title)
        top.addStretch()

        self.status = QLabel("● ACTIVE")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setFixedWidth(180)
        self.status.setStyleSheet(PILL)
        top.addWidget(self.status)

        top.addStretch()

        self.clock = QLabel()
        self.clock.setStyleSheet(
            "color:white;font-size:28px;font-weight:bold;"
        )
        top.addWidget(self.clock)

        root.addLayout(top)

        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        self.update_time()

        # ---------- BODY ----------
        body = QHBoxLayout()
        body.setSpacing(18)

        # LEFT SIDE
        left = QVBoxLayout()
        left.setSpacing(18)

        camera_card = QFrame()
        camera_card.setMinimumSize(950, 620)
        camera_card.setStyleSheet(CARD)

        cam_layout = QVBoxLayout(camera_card)

        cam_title = QLabel("AI CAMERA")
        cam_title.setStyleSheet(
            "color:#22c55e;font-size:18px;font-weight:bold;"
        )
        cam_layout.addWidget(cam_title)

        self.camera = QLabel("LIVE CAMERA FEED")
        self.camera.setAlignment(Qt.AlignCenter)
        self.camera.setStyleSheet("""
            background:#111827;
            border-radius:18px;
            color:#64748b;
            font-size:28px;
            font-weight:bold;
        """)
        cam_layout.addWidget(self.camera)

        left.addWidget(camera_card)

        # ALERT STRIP
        strip = QFrame()
        strip.setFixedHeight(120)
        strip.setStyleSheet(CARD)

        strip_layout = QHBoxLayout(strip)

        for txt in ["EYE", "YAWN", "LOOK AWAY", "PHONE"]:
            box = QLabel(f"{txt}\nNormal")
            box.setAlignment(Qt.AlignCenter)
            box.setStyleSheet("""
                background:#0f172a;
                border-radius:16px;
                color:white;
                font-size:16px;
                padding:14px;
            """)
            strip_layout.addWidget(box)

        left.addWidget(strip)

        body.addLayout(left, 3)

        # RIGHT SIDE
        right = QGridLayout()
        right.setSpacing(18)

        self.focus = Card("FOCUS SCORE", "100", "#22c55e")
        right.addWidget(self.focus, 0, 0)

        self.trip = Card("TRIP SUMMARY", "Excellent", "#38bdf8")
        right.addWidget(self.trip, 0, 1)

        self.overview = Card("STATUS OVERVIEW", "SAFE", "#22c55e")
        right.addWidget(self.overview, 1, 0)

        self.alerts = Card("RECENT ALERTS", "No alerts", "#f97316")
        right.addWidget(self.alerts, 1, 1)

        body.addLayout(right, 2)

        root.addLayout(body)

        # FOOTER
        footer = QLabel("Drive Safe. Stay Alert. Reach Alive.")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            "color:#22c55e;font-size:18px;font-weight:bold;"
        )
        root.addWidget(footer)

    def update_time(self):
        self.clock.setText(QTime.currentTime().toString("hh:mm:ss"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SafeDriveProUI()
    win.show()
    sys.exit(app.exec())