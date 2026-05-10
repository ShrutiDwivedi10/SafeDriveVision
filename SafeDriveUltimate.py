import sys
import cv2
import dlib
import torch
import math
import time
import threading
import os
import sqlite3
from datetime import datetime

import numpy as np
import pygame
from scipy.spatial import distance as dist

from PySide6.QtGui import QImage, QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame
)
from PySide6.QtCore import Qt, QTimer, QTime
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
# -------------------- AI HELPERS --------------------
pygame.mixer.init()

sounds = {
    'eye': ('./eye.mp3', 10),
    'regarder': ('./regarder.mp3', 10),
    'reposer': ('./reposer.mp3', 15),
    'phone': ('./phone.mp3', 15),
    'welcome': ('./s1.mp3', 0),
    'welcome_eng': ('./welcomeengl.mp3', 0)
}

last_played = {key: 0 for key in sounds}


def play_sound(sound_key):
    audio_file, delay = sounds[sound_key]
    now = time.time()

    if now - last_played[sound_key] > delay:
        try:
            sound = pygame.mixer.Sound(audio_file)
            sound.play()
            last_played[sound_key] = now
            print(f"[VOICE] {sound_key}")
        except Exception as e:
            print("Audio error:", e)


def sound_thread(sound_key):
    thread = threading.Thread(
        target=play_sound,
        args=(sound_key,),
        daemon=True
    )
    thread.start()


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


def calculate_head_angle(eye_left, eye_right, nose_tip):
    eye_center = (eye_left + eye_right) / 2
    vector_nose = nose_tip - eye_center
    vector_horizontal = (eye_right - eye_left)

    vector_nose_normalized = (
        vector_nose / np.linalg.norm(vector_nose)
    )

    vector_horizontal_normalized = (
        vector_horizontal / np.linalg.norm(vector_horizontal)
    )

    angle_rad = np.arccos(
        np.clip(
            np.dot(
                vector_nose_normalized,
                vector_horizontal_normalized
            ),
            -1.0,
            1.0
        )
    )

    return np.degrees(angle_rad)


def save_event(frame, event_type):
    os.makedirs("captures", exist_ok=True)

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    filename = (
        f"captures/{event_type}_{timestamp}.jpg"
    )

    cv2.imwrite(filename, frame)

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


def log_alert(alert_type, focus_score):
    conn = sqlite3.connect("safedrive.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO alerts(time, alert_type, focus_score) VALUES(?,?,?)",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            alert_type,
            int(focus_score)
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
            int(score)
        )
    )

    conn.commit()
    conn.close()    

def generate_report():
    conn = sqlite3.connect("safedrive.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT alert_type, COUNT(*)
        FROM alerts
        GROUP BY alert_type
    """)
    rows = cur.fetchall()

    cur.execute("""
        SELECT AVG(focus_score)
        FROM alerts
    """)
    avg_focus = cur.fetchone()[0]

    conn.close()

    report = {
        "Eyes closed": 0,
        "Yawning": 0,
        "Phone detected": 0,
        "Look away": 0,
        "Driver not looking": 0
    }

    for alert, count in rows:
        report[alert] = count

    avg_focus = int(avg_focus) if avg_focus else 100

    risk = "Low"
    if avg_focus < 80:
        risk = "Moderate"
    if avg_focus < 50:
        risk = "High"

    print("\n===== DRIVER REPORT =====")
    for k, v in report.items():
        print(f"{k}: {v}")
    print("Average focus:", avg_focus)
    print("Risk level:", risk)
    print("=========================\n")     

def reset_session():
    conn = sqlite3.connect("safedrive.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()     
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

        self.reset_btn = QLabel("RESET")
        self.reset_btn.setStyleSheet("""
            background:#dc2626;
            color:white;
            padding:6px 14px;
            border-radius:14px;
            font-weight:bold;
        """)
        self.reset_btn.mousePressEvent = self.reset_clicked

        top.addSpacing(20)
        top.addWidget(self.reset_btn)
        top.addSpacing(20)
        top.addWidget(self.clock)

        main.addLayout(top)

        # clock update
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)

        self.cap = cv2.VideoCapture(0)

        # AI models
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

        # counters
        self.focus_score = 100
        self.yawn_count = 0
        self.phone_count = 0
        self.lookaway_count = 0
        self.eye_close_count = 0

        self.status_text = "SAFE"
        self.recent_alerts = []

        # internal counters
        self.COUNTER1 = 0
        self.COUNTER2 = 0
        self.COUNTER3 = 0
        self.COUNTER_YAWN = 0
        self.COUNTER_FACE = 0
        self.COUNTER_LOOK = 0
        self.repeat_counter = 0

        self.last_phone_alert = 0
        self.last_lookaway_alert = 0
        self.last_eye_alert = 0
        self.last_yawn_alert = 0

        self.last_focus_log = time.time()
        sound_thread("welcome_eng")

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
        # BOTTOM ALERT CHIPS (LIVE)
        chips = QHBoxLayout()

        def make_chip():
            chip = QLabel("0")
            chip.setAlignment(Qt.AlignCenter)
            chip.setMinimumHeight(44)
            chip.setStyleSheet("""
                background:#111827;
                border:1px solid #334155;
                padding:8px 18px;
                border-radius:18px;
                color:white;
                font-size:15px;
                font-weight:bold;
            """)
            return chip

        self.eye_chip = make_chip()
        self.yawn_chip = make_chip()
        self.phone_chip = make_chip()
        self.look_chip = make_chip()

        chips.addWidget(self.eye_chip)
        chips.addWidget(self.yawn_chip)
        chips.addWidget(self.phone_chip)
        chips.addWidget(self.look_chip)

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

        print("Session reset")

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        img = frame.copy()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
        faces = self.detector(gray, 0)

            # YOLO phone detection
        results = self.model(img)
        detections = results.xyxy[0]

        for detection in detections:
            if int(detection[5]) == 67:
                self.COUNTER2 += 1

                if self.COUNTER2 >= 3:
                    if time.time() - self.last_phone_alert > 5:
                        self.phone_count += 1
                        self.focus_score = max(0, self.focus_score - 15)
                        self.last_phone_alert = time.time()

                        sound_thread("phone")
                        save_event(img, "phone")

                        self.recent_alerts.append("Phone detected")
                        log_alert("Phone detected", self.focus_score)
                    self.COUNTER2 = 0

        if len(faces) == 0:
            self.COUNTER_FACE += 1

            if self.COUNTER_FACE >= 40:
                if time.time() - self.last_lookaway_alert > 3:
                    self.lookaway_count += 1
                    self.focus_score = max(0, self.focus_score - 3)
                    self.last_lookaway_alert = time.time()

                    sound_thread("regarder")   # ADD THIS
                    save_event(img, "lookaway")

                    self.recent_alerts.append("Driver not looking")
                    log_alert("Driver not looking", self.focus_score)
                self.COUNTER_FACE = 0
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

            # eyes closed
           
            if ear < 0.28:
                self.COUNTER1 += 1

                if self.COUNTER1 >= 2:
                    if time.time() - self.last_eye_alert > 4:
                        self.eye_close_count += 1
                        self.focus_score = max(0, self.focus_score - 10)
                        self.last_eye_alert = time.time()
                        
                        sound_thread("eye")
                        save_event(img, "eyesclosed")

                        self.recent_alerts.append("Eyes closed")
                        log_alert("Eyes closed", self.focus_score)

                    self.COUNTER1 = 0
            else:
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
                    sound_thread("reposer")   # ADD THIS
                    save_event(img, "yawn")
                    self.recent_alerts.append("Yawning")
                    log_alert("Yawning", self.focus_score)
                self.COUNTER_YAWN = 0


        # look away detection
        eye_left = pts[36]
        eye_right = pts[45]
        nose_tip = pts[33]

        eye_center_x = (eye_left[0] + eye_right[0]) / 2
        face_width = abs(eye_right[0] - eye_left[0])
        nose_shift = abs(nose_tip[0] - eye_center_x)

        # ratio independent of face size
        look_ratio = nose_shift / face_width

        # strong turn -> instant alert
        if look_ratio > 0.18:
            if time.time() - self.last_lookaway_alert > 2:
                print("LOOK AWAY CONFIRMED")

                self.lookaway_count += 1
                self.focus_score = max(0, self.focus_score - 8)
                self.last_lookaway_alert = time.time()

                sound_thread("regarder")
                save_event(img, "lookaway")
                self.recent_alerts.append("Look away")
                log_alert("Look away", self.focus_score)
        # keep chip live
        self.COUNTER_LOOK = int(look_ratio * 20)

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

                # recover score slowly when attentive
\
        if len(faces) > 0:
            if (
                self.COUNTER1 == 0
                and self.COUNTER2 == 0
                and self.COUNTER_LOOK == 0
                and self.COUNTER_YAWN == 0
            ):
                self.focus_score = min(
                    100,
                    float(self.focus_score) + 0.08
                )

    # keep integer for UI
\

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

        self.focus.findChildren(QLabel)[0].setText(
            str(int(self.focus_score))
        )

        self.eye_chip.setText(
            f"EYES  {max(self.eye_close_count, self.COUNTER1)}"
        )

        self.yawn_chip.setText(
            f"YAWN  {max(self.yawn_count, self.COUNTER_YAWN)}"
        )

        self.phone_chip.setText(
            f"PHONE  {max(self.phone_count, self.COUNTER2)}"
        )

        live_look = max(
            self.lookaway_count,
            self.COUNTER_LOOK,
            self.COUNTER_FACE
        )

        self.look_chip.setText(f"LOOK  {live_look}")
        def chip_style(color, active):
            glow = f"2px solid {color}" if active else "1px solid #334155"
            bg = "#1e293b" if active else "#111827"
            return f"""
                QLabel {{
                    background:{bg};
                    border:{glow};
                    padding:8px 18px;
                    border-radius:18px;
                    color:white;
                    font-size:15px;
                    font-weight:bold;
                }}
            """

        self.eye_chip.setStyleSheet(
            chip_style("#ef4444", self.COUNTER1 > 0)
        )
        self.yawn_chip.setStyleSheet(
            chip_style("#facc15", self.COUNTER_YAWN > 0)
        )
        self.phone_chip.setStyleSheet(
            chip_style("#38bdf8", self.COUNTER2 > 0)
        )
        self.look_chip.setStyleSheet(
            chip_style("#f97316", self.COUNTER_LOOK > 0 or self.COUNTER_FACE > 0)
        )

        if time.time() - self.last_focus_log > 5:
            log_focus(self.focus_score)
            self.last_focus_log = time.time()
    def update_time(self):
        current = QTime.currentTime().toString("hh:mm:ss")
        self.clock.setText(current)

# -------------------- RUN --------------------
init_db()

app = QApplication(sys.argv)
window = SafeDriveUI()
window.show()
exit_code = app.exec()
generate_report()
sys.exit(exit_code)
