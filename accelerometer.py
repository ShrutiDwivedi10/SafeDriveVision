# accelerometer.py

import requests
import time


def get_phone_acceleration():
    try:
        # Replace this with your PHYPhox phone IP
        phone_ip = "192.168.1.7"

        # PHYPhox API URL
        url = f"http://192.168.29.224:8080/get?accX&accY&accZ"

        response = requests.get(url)
        data = response.json()

        # Fetch acceleration values
        acc_x = data["buffer"]["accX"]["buffer"][0]
        acc_y = data["buffer"]["accY"]["buffer"][0]
        acc_z = data["buffer"]["accZ"]["buffer"][0]

        print("===================================")
        print("LIVE ACCELEROMETER DATA")
        print("===================================")
        print(f"X Axis : {acc_x}")
        print(f"Y Axis : {acc_y}")
        print(f"Z Axis : {acc_z}")
        print("===================================")

        return acc_x, acc_y, acc_z

    except Exception as e:
        print("Error fetching accelerometer data")
        print("Reason:", e)
        return 0, 0, 0


def detect_accident():
    acc_x, acc_y, acc_z = get_phone_acceleration()

    # Threshold for sudden movement / crash detection
    threshold = 15

    if abs(acc_x) > threshold or abs(acc_y) > threshold or abs(acc_z) > threshold:
        print("🚨 POSSIBLE ACCIDENT DETECTED!")
        return True
    else:
        print("Normal Driving Condition")
        return False


if __name__ == "__main__":
    while True:
        detect_accident()
        time.sleep(5)