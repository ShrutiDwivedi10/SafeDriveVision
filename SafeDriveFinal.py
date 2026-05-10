import sys
import cv2
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QFont
import dlib
import torch
import numpy as np
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

        self.cap = cv2.VideoCapture(0)
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(
            "./shape_predictor_81_face_landmarks (1).dat"
        )

        self.model = torch.hub.load(
            "ultralytics/yolov5",
            "custom",
            path="./weights/yolov5m.pt",
            source="github",
            force_reload=False
        )
        self.focus_score = 100
        self.yawn_count = 0
        self.phone_count = 0
        self.lookaway_count = 0
        self.eye_close_count = 0
        self.status_text = "SAFE"
        self.recent_alerts = []

        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self.update_frame)
        self.camera_timer.start(30)

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
 

        self.camera_label = QLabel(self.camera)
        self.camera_label.setGeometry(20, 60, 860, 560)
        self.camera_label.setStyleSheet("border:none;")
        self.camera_label.setAlignment(Qt.AlignCenter)
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

        self.focus = FocusCircle("100")
        right.addWidget(self.focus, 0, 0, 1, 2)

        self.status_card = Card("STATUS", "SAFE")
        right.addWidget(self.status_card, 1, 0)

        self.yawn_card = Card("YAWNS", "0", "#facc15")
        right.addWidget(self.yawn_card, 1, 1)

        self.look_card = Card("LOOK AWAY", "0", "#f97316")
        right.addWidget(self.look_card, 2, 0)

        self.phone_card = Card("PHONE", "0", "#38bdf8")
        right.addWidget(self.phone_card, 2, 1)

        self.alerts_card = Card("RECENT ALERTS", "No alerts", "#ef4444")
        right.addWidget(self.alerts_card, 3, 0, 1, 2)
       

        body.addLayout(left, 3)
        body.addLayout(right, 1)

        main.addLayout(body)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        img = frame.copy()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
        faces = self.detector(gray, 0)

        results = self.model(img)
        detections = results.xyxy[0]

        # phone detection
        for detection in detections:
            if int(detection[5]) == 67:
                self.phone_count += 1
                self.focus_score = max(0, self.focus_score - 5)

                if len(self.recent_alerts) == 0 or self.recent_alerts[-1] != "Phone detected":
                    self.recent_alerts.append("Phone detected") 

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (860, 560))

        h, w, ch = frame.shape
        bytes_per_line = ch * w

        img = QImage(
            frame.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888
        )

        self.camera_label.setPixmap(
            QPixmap.fromImage(img)
        )
        # decide status
        self.status_text = "SAFE"

        if self.focus_score < 80:
            self.status_text = "WARNING"

        if self.focus_score < 50:
            self.status_text = "HIGH RISK"
           # update UI from live counters
        status = self.status_text

        self.status_card.findChildren(QLabel)[1].setText(status)
        self.yawn_card.findChildren(QLabel)[1].setText(str(self.yawn_count))
        self.look_card.findChildren(QLabel)[1].setText(str(self.lookaway_count))
        self.phone_card.findChildren(QLabel)[1].setText(str(self.phone_count))

        recent = "\n".join(self.recent_alerts[-3:]) if self.recent_alerts else "No alerts"
        self.alerts_card.findChildren(QLabel)[1].setText(recent)

        self.focus.findChildren(QLabel)[0].setText(str(self.focus_score))

    def update_time(self):
        current = QTime.currentTime().toString("hh:mm:ss")
        self.clock.setText(current)


# -------------------- RUN --------------------
app = QApplication(sys.argv)
window = SafeDriveUI()
window.show()
sys.exit(app.exec())
