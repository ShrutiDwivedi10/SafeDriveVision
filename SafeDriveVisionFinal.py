import sys
import cv2
import dlib
import torch
import time
import threading
import os
import sqlite3
from datetime import datetime

import numpy as np
import pygame
from scipy.spatial import distance as dist

from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QImage, QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
)

# ===================== STYLES =====================
BG = "#030712"
CARD_BG = "#08111f"
BORDER = "#10243f"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
GREEN = "#22c55e"
GLOW_GREEN = "#4ade80"
YELLOW = "#facc15"
ORANGE = "#fb923c"
BLUE = "#38bdf8"
RED = "#ef4444"

CARD_STYLE = f"""
QFrame {{
    background:{CARD_BG};
    border:1px solid #16355a;
    border-radius:22px;
}}
QFrame:hover {{
    border:1px solid {GLOW_GREEN};
}}
QLabel {{
    color:{TEXT};
    border:none;
}}
"""

PILL_STYLE = f"""
QLabel {{
    background:#0b1728;
    border:1px solid {BORDER};
    border-radius:16px;
    padding:8px 18px;
    color:{GREEN};
    font-size:16px;
    font-weight:bold;
}}
"""

# ===================== AUDIO =====================
pygame.mixer.init()

sounds = {
    "eye": ("./eye.mp3", 10),
    "regarder": ("./regarder.mp3", 10),
    "reposer": ("./reposer.mp3", 15),
    "phone": ("./phone.mp3", 15),
    "welcome_eng": ("./welcomeengl.mp3", 0),
}

last_played = {k: 0 for k in sounds}


def play_sound(key):
    audio_file, delay = sounds[key]
    now = time.time()

    if now - last_played[key] > delay:
        try:
            pygame.mixer.Sound(audio_file).play()
            last_played[key] = now
        except:
            pass


def sound_thread(key):
    threading.Thread(
        target=play_sound,
        args=(key,),
        daemon=True
    ).start()


# ===================== HELPERS =====================
def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)


def mouth_aspect_ratio(mouth):
    A = dist.euclidean(mouth[2], mouth[10])
    B = dist.euclidean(mouth[4], mouth[8])
    C = dist.euclidean(mouth[0], mouth[6])
    return (A + B) / (2.0 * C)


def save_event(frame, event_type):
    os.makedirs("captures", exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    cv2.imwrite(f"captures/{event_type}_{ts}.jpg", frame)


# ===================== DATABASE =====================
def init_db():
    conn = sqlite3.connect("safedrive.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            alert_type TEXT,
            focus_score INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS focus_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            focus_score INTEGER
        )
    """)

    conn.commit()
    conn.close()


def log_alert(alert_type, focus):
    conn = sqlite3.connect("safedrive.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO alerts(time, alert_type, focus_score) VALUES(?,?,?)",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            alert_type,
            int(focus),
        )
    )

    conn.commit()
    conn.close()


def log_focus(score):
    conn = sqlite3.connect("safedrive.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO focus_history(time, focus_score) VALUES(?,?)",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            int(score),
        )
    )

    conn.commit()
    conn.close()


def reset_session():
    conn = sqlite3.connect("safedrive.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM alerts")
    cur.execute("DELETE FROM focus_history")
    conn.commit()
    conn.close()

# ===================== UI COMPONENTS =====================
class MetricCard(QFrame):
    def __init__(self, title, value="", color=GREEN):
        super().__init__()
        self.setStyleSheet(CARD_STYLE)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)

        t = QLabel(title)
        t.setStyleSheet(f"color:{MUTED};font-size:14px;font-weight:bold;")
        lay.addWidget(t)

        self.value = QLabel(value)
        self.value.setStyleSheet(
            f"color:{color};font-size:28px;font-weight:bold;"
        )
        lay.addWidget(self.value)

        lay.addStretch()


class FocusCircle(QFrame):
    def __init__(self):
        super().__init__()

        self.score_value = 100
        self.setFixedSize(210, 210)

        self.score = QLabel("100", self)
        self.score.setAlignment(Qt.AlignCenter)
        self.score.setGeometry(0, 55, 210, 60)
        self.score.setStyleSheet(f"""
            color:{GREEN};
            font-size:48px;
            font-weight:bold;
            background:transparent;
            border:none;
        """)

        self.label = QLabel("FOCUS SCORE", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(0, 110, 210, 35)
        self.label.setStyleSheet(f"""
            color:{MUTED};
            font-size:14px;
            font-weight:bold;
            background:transparent;
            border:none;
        """)

    def setScore(self, value):
        self.score_value = max(0, min(100, int(value)))
        self.score.setText(str(self.score_value))
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QColor, QPen

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # background ring
        pen = QPen(QColor("#17304f"), 14)
        painter.setPen(pen)
        painter.drawEllipse(20, 20, 170, 170)

        # progress color
        if self.score_value >= 80:
            ring_color = GREEN
        elif self.score_value >= 50:
            ring_color = YELLOW
        else:
            ring_color = RED

        # progress ring
        pen = QPen(QColor(ring_color), 14)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        angle = int((self.score_value / 100) * 360 * 16)

        painter.drawArc(
            20,
            20,
            170,
            170,
            90 * 16,
            -angle
        )


class AlertChip(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(64)
        self.setStyleSheet(f"""
            background:#0b1728;
            border:1px solid {BORDER};
            border-radius:18px;
            color:white;
            font-size:16px;
            font-weight:bold;
        """)


# ===================== MAIN WINDOW =====================
class SafeDriveVision(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SafeDrive Vision Final")
        self.resize(1700, 950)
        self.setStyleSheet(f"background:{BG};")

        # engine state
        self.focus_score = 100
        self.yawn_count = 0
        self.phone_count = 0
        self.lookaway_count = 0
        self.eye_close_count = 0
        self.recent_alerts = []
        self.status_text = "SAFE"

        self.COUNTER1 = 0
        self.COUNTER2 = 0
        self.COUNTER_YAWN = 0
        self.COUNTER_FACE = 0
        self.COUNTER_LOOK = 0

        self.last_phone_alert = 0
        self.last_lookaway_alert = 0
        self.last_eye_alert = 0
        self.last_yawn_alert = 0
        self.last_focus_log = time.time()
        self.last_whatsapp_alert_time = 0

        # models
        self.cap = cv2.VideoCapture(0)
        # self.cap = cv2.VideoCapture("http://192.168.29.224:8080/video")
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

        sound_thread("welcome_eng")

        # ---------- LAYOUT ----------
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(18)

        # top bar
        top = QHBoxLayout()

        title_box = QVBoxLayout()

        title = QLabel("SafeDrive Vision")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color:white;")

        subtitle = QLabel("AI Driver Monitoring Dashboard")
        subtitle.setStyleSheet(f"color:{MUTED};font-size:14px;")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        top.addLayout(title_box)
        top.addStretch()

        self.status_badge = QLabel("● ACTIVE")
        self.status_badge.setStyleSheet(PILL_STYLE)
        top.addWidget(self.status_badge)

        self.reset_btn = QLabel("RESET")
        self.reset_btn.setAlignment(Qt.AlignCenter)
        self.reset_btn.setStyleSheet(f"""
            background:#7f1d1d;
            border:1px solid #991b1b;
            border-radius:16px;
            padding:8px 18px;
            color:white;
            font-weight:bold;
        """)
        self.reset_btn.mousePressEvent = self.reset_clicked
        top.addWidget(self.reset_btn)

        self.clock = QLabel()
        self.clock.setStyleSheet(
            "color:white;font-size:26px;font-weight:bold;"
        )
        top.addWidget(self.clock)

        root.addLayout(top)

        # body
        body = QHBoxLayout()
        body.setSpacing(18)

        # left
        left = QVBoxLayout()

        cam_card = QFrame()
        cam_card.setMinimumSize(760, 520)
        cam_card.setStyleSheet(CARD_STYLE)

        cam_layout = QVBoxLayout(cam_card)

        cam_title = QLabel("LIVE DRIVER FEED")
        cam_title.setStyleSheet(
            f"color:{GREEN};font-size:18px;font-weight:bold;"
        )
        cam_layout.addWidget(cam_title)

        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("""
            background:#111827;
            border-radius:18px;
            color:#64748b;
            font-size:26px;
            font-weight:bold;
        """)
        cam_layout.addWidget(self.camera_label,1)

        left.addWidget(cam_card)

        chips = QHBoxLayout()

        self.eye_chip = AlertChip("👁  EYE")
        self.yawn_chip = AlertChip("😮  YAWN")
        self.look_chip = AlertChip("👀  LOOK")
        self.phone_chip = AlertChip("📱  PHONE")

        chips.addWidget(self.eye_chip)
        chips.addWidget(self.yawn_chip)
        chips.addWidget(self.look_chip)
        chips.addWidget(self.phone_chip)

        left.addLayout(chips)

        body.addLayout(left, 3)

        # right
        right = QGridLayout()
        right.setVerticalSpacing(18)
        right.setHorizontalSpacing(18)
        right.setSpacing(18)

        self.focus_circle = FocusCircle()
        right.addWidget(self.focus_circle, 0, 0, 2, 2)

        self.status_card = MetricCard("STATUS", "SAFE", GREEN)
        right.addWidget(self.status_card, 2, 0)

        self.yawn_card = MetricCard("YAWNS", "0", YELLOW)
        right.addWidget(self.yawn_card, 2, 1)

        self.look_card = MetricCard("LOOK AWAY", "0", ORANGE)
        right.addWidget(self.look_card, 3, 0)

        self.phone_card = MetricCard("PHONE", "0", BLUE)
        right.addWidget(self.phone_card, 3, 1)

        self.trip_card = MetricCard("TRIP SUMMARY", "Excellent", BLUE)
        right.addWidget(self.trip_card, 4, 0)

        self.overview_card = MetricCard("STATUS OVERVIEW", "Focused", GREEN)
        right.addWidget(self.overview_card, 4, 1)

        self.alert_card = MetricCard("RECENT ALERTS", "No alerts", RED)
        right.addWidget(self.alert_card, 5, 0, 1, 2)

        body.addLayout(right, 2)
        root.addLayout(body)

        # timers
        clock_timer = QTimer(self)
        clock_timer.timeout.connect(self.update_time)
        clock_timer.start(1000)
        self.update_time()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def reset_clicked(self, event):
        reset_session()

        self.focus_score = 100
        self.yawn_count = 0
        self.phone_count = 0
        self.lookaway_count = 0
        self.eye_close_count = 0
        self.recent_alerts.clear()

        self.COUNTER1 = 0
        self.COUNTER2 = 0
        self.COUNTER_YAWN = 0
        self.COUNTER_FACE = 0
        self.COUNTER_LOOK = 0

    def update_time(self):
        self.clock.setText(
            QTime.currentTime().toString("hh:mm:ss")
        )

    def closeEvent(self, event):
        self.cap.release()
        pygame.mixer.quit()
        event.accept()
        
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        img = frame.copy()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray, 0)

        # phone detection
        results = self.model(img)
        detections = results.xyxy[0]
        phone_found = False

        for detection in detections:
            if int(detection[5]) == 67:
                phone_found = True
                self.COUNTER2 += 1

                if self.COUNTER2 >= 3:
                    if time.time() - self.last_phone_alert > 5:
                        self.phone_count += 1
                        self.focus_score = max(0, self.focus_score - 15)
                        self.last_phone_alert = time.time()

                        sound_thread("phone")
                        save_event(img, "phone")
                        stamp = datetime.now().strftime("%H:%M:%S")
                        self.recent_alerts.append(f"{stamp}  Phone detected")
                        self.recent_alerts = self.recent_alerts[-5:]
                        log_alert("Phone detected", self.focus_score)

                    self.COUNTER2 = 0

        if not phone_found:
            self.COUNTER2 = 0

        if len(faces) == 0:
            self.COUNTER_FACE += 1
        else:
            self.COUNTER_FACE = 0

        for face in faces:
            landmarks = self.predictor(gray, face)
            pts = np.array([(p.x, p.y) for p in landmarks.parts()])

            left_eye = pts[36:42]
            right_eye = pts[42:48]
            mouth = pts[48:68]

            ear = (
                eye_aspect_ratio(left_eye)
                + eye_aspect_ratio(right_eye)
            ) / 2.0

            mar = mouth_aspect_ratio(mouth)

            # eyes
            if ear < 0.23:
                self.COUNTER1 += 1
            else:
                self.COUNTER1 = 0

            if self.COUNTER1 >= 18:
                if time.time() - self.last_eye_alert > 4:
                    self.eye_close_count += 1
                    self.focus_score = max(0, self.focus_score - 10)
                    self.last_eye_alert = time.time()

                    sound_thread("eye")
                    save_event(img, "eyesclosed")
                    stamp = datetime.now().strftime("%H:%M:%S")
                    self.recent_alerts.append(f"{stamp}  Eyes closed")
                    self.recent_alerts = self.recent_alerts[-5:]
                    log_alert("Eyes closed", self.focus_score)

                self.COUNTER1 = 0

            # yawn
            if mar > 0.40:
                self.COUNTER_YAWN += 1
            else:
                self.COUNTER_YAWN = 0

            if self.COUNTER_YAWN >= 5:
                if time.time() - self.last_yawn_alert > 5:
                    self.yawn_count += 1
                    self.focus_score = max(0, self.focus_score - 5)
                    self.last_yawn_alert = time.time()

                    sound_thread("reposer")
                    save_event(img, "yawn")
                    stamp = datetime.now().strftime("%H:%M:%S")
                    self.recent_alerts.append(f"{stamp}  Yawning")
                    self.recent_alerts = self.recent_alerts[-5:]
                    log_alert("Yawning", self.focus_score)

                self.COUNTER_YAWN = 0

            # look away
            eye_left = pts[36]
            eye_right = pts[45]
            nose_tip = pts[33]

            eye_center_x = (eye_left[0] + eye_right[0]) / 2
            face_width = abs(eye_right[0] - eye_left[0])
            nose_shift = abs(nose_tip[0] - eye_center_x)

            look_ratio = nose_shift / max(face_width, 1)

            if look_ratio > 0.18:
                if time.time() - self.last_lookaway_alert > 2:
                    self.lookaway_count += 1
                    self.focus_score = max(0, self.focus_score - 8)
                    self.last_lookaway_alert = time.time()

                    sound_thread("regarder")
                    save_event(img, "lookaway")
                    stamp = datetime.now().strftime("%H:%M:%S")
                    self.recent_alerts.append(f"{stamp}  Look away")
                    self.recent_alerts = self.recent_alerts[-5:]
                    log_alert("Look away", self.focus_score)

            self.COUNTER_LOOK = int(look_ratio * 20)

        # recover slowly
        if len(faces) > 0:
            if (
                self.COUNTER1 == 0
                and self.COUNTER2 == 0
                and self.COUNTER_LOOK == 0
                and self.COUNTER_YAWN == 0
            ):
                self.focus_score = min(100, self.focus_score + 0.08)

            # status
            if self.focus_score >= 80:
                self.status_text = "SAFE"
            elif self.focus_score >= 50:
                self.status_text = "WARNING"
            else:
                self.status_text = "HIGH RISK"
                
            if self.status_text == "WARNING" and int(self.focus_score) <= 59:
                if time.time() - self.last_whatsapp_alert_time > 100:
                    self.last_whatsapp_alert_time = time.time()
                    def alert_task():
                        try:
                            from alert_system import send_whatsapp_alert
                            send_whatsapp_alert("Driver focus score dropped below 60 (WARNING)")
                        except Exception as e:
                            print(f"Error sending WhatsApp alert: {e}")
                    threading.Thread(target=alert_task, daemon=True).start()

        # ---------- AI OVERLAY ----------
        if len(faces) > 0:
            face = faces[0]

            x1 = face.left()
            y1 = face.top()
            x2 = face.right()
            y2 = face.bottom()

            color = (34, 197, 94)
            glow = (70, 180, 110)
            L = 35

            # glass panel
            overlay = frame.copy()
            cv2.rectangle(overlay, (20, 20), (280, 185), (10, 25, 45), -1)
            cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

            # glowing brackets
            # top-left
            cv2.line(frame, (x1, y1), (x1 + L, y1), glow, 4)
            cv2.line(frame, (x1, y1), (x1 + L, y1), color, 3)
            cv2.line(frame, (x1, y1), (x1, y1 + L), glow, 4)
            cv2.line(frame, (x1, y1), (x1, y1 + L), color, 3)

            # top-right
            cv2.line(frame, (x2, y1), (x2 - L, y1), glow, 4)
            cv2.line(frame, (x2, y1), (x2 - L, y1), color, 3)
            cv2.line(frame, (x2, y1), (x2, y1 + L), glow, 4)
            cv2.line(frame, (x2, y1), (x2, y1 + L), color, 3)

            # bottom-left
            cv2.line(frame, (x1, y2), (x1 + L, y2), glow, 4)
            cv2.line(frame, (x1, y2), (x1 + L, y2), color, 3)
            cv2.line(frame, (x1, y2), (x1, y2 - L), glow, 4)
            cv2.line(frame, (x1, y2), (x1, y2 - L), color, 3)

            # bottom-right
            cv2.line(frame, (x2, y2), (x2 - L, y2), glow, 4)
            cv2.line(frame, (x2, y2), (x2 - L, y2), color, 3)
            cv2.line(frame, (x2, y2), (x2, y2 - L), glow, 4)
            cv2.line(frame, (x2, y2), (x2, y2 - L), color, 3)

            # glowing title
            cv2.putText(frame, "Face Detected",
                        (x1, y1 - 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.75, glow, 2)

            cv2.putText(frame, "Face Detected",
                        (x1, y1 - 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.75, color, 2)

            # glowing metrics
            metrics = [
                f"EAR: {ear:.2f}",
                f"MAR: {mar:.2f}",
                f"LOOK: {look_ratio:.2f}",
                f"FOCUS: {int(self.focus_score)}"
            ]

            y = 55
            for txt in metrics:
                cv2.putText(frame, txt, (35, y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.82, glow, 2)

                cv2.putText(frame, txt, (35, y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.82, color, 2)

                y += 35   
        # camera render
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (980, 620))

        h, w, ch = rgb.shape
        qt = QImage(
            rgb.data,
            w,
            h,
            ch * w,
            QImage.Format_RGB888
        )

        self.camera_label.setPixmap(QPixmap.fromImage(qt))

        # UI updates
        self.focus_circle.setScore(self.focus_score)
        self.status_card.value.setText(self.status_text)
        self.yawn_card.value.setText(str(self.yawn_count))
        self.look_card.value.setText(str(self.lookaway_count))
        self.phone_card.value.setText(str(self.phone_count))
        
        total_alerts = (
            self.eye_close_count
            + self.yawn_count
            + self.phone_count
            + self.lookaway_count
        )

        self.trip_card.value.setText(
            f"Avg {int(self.focus_score)} | Alerts {total_alerts}"
        )

        if self.focus_score >= 80:
            self.overview_card.value.setText("Highly Focused")
        elif self.focus_score >= 50:
            self.overview_card.value.setText("Moderate")
        else:
            self.overview_card.value.setText("Distracted")
        recent = (
            "\n".join(self.recent_alerts[-3:])
            if self.recent_alerts
            else "No alerts"
        )
        self.alert_card.value.setText(recent)

        self.eye_chip.setText(f"👁  EYE {max(self.eye_close_count, self.COUNTER1)}")
        self.yawn_chip.setText(f"😮  YAWN {max(self.yawn_count, self.COUNTER_YAWN)}")
        self.look_chip.setText(f"👀  LOOK {self.lookaway_count}")
        self.phone_chip.setText(f"📱  PHONE {max(self.phone_count, self.COUNTER2)}")

        if time.time() - self.last_focus_log > 5:
            log_focus(self.focus_score)
            self.last_focus_log = time.time()


# ===================== RUN =====================
if __name__ == "__main__":
    init_db()

    app = QApplication(sys.argv)
    win = SafeDriveVision()
    win.show()
    sys.exit(app.exec())


