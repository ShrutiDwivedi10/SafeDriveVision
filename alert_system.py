import pywhatkit
import pyautogui
import time
import geocoder
from datetime import datetime
from accelerometer import get_phone_acceleration

def get_live_location():
    g = geocoder.ip('me')

    if g.latlng:
        latitude, longitude = g.latlng
        google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
        return google_maps_link
    else:
        return "Location not found"
    
    
def get_live_location():
    g = geocoder.ip('me')

    if g.latlng:
        latitude, longitude = g.latlng
        google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
        return google_maps_link
    else:
        return "Location not found"


def calculate_accident_percentage(acc_x, acc_y, acc_z):
    """
    Calculate accident risk percentage based on acceleration
    """

    total_acc = abs(acc_x) + abs(acc_y) + abs(acc_z)

    if total_acc < 10:
        return 20, "Normal Driving"

    elif total_acc < 20:
        return 50, "Medium Risk"

    elif total_acc < 30:
        return 75, "High Risk"

    else:
        return 95, "Critical Accident Risk"


def get_estimated_speed(acc_x, acc_y):
    """
    Demo speed estimation using acceleration
    """

    speed = int((abs(acc_x) + abs(acc_y)) * 5)

    if speed < 20:
        speed = 20

    return speed



def send_whatsapp_alert(alert_reason="Driver Sleep Detected"):
    family_members = [
        "+919691451796",
        "+918839936283",
        "+918770479633"
    ]

    current_time = datetime.now().strftime("%H:%M:%S")
    live_location = get_live_location()
    
     # Get Accelerometer Data
    acc_x, acc_y, acc_z = get_phone_acceleration()

    # Calculate speed + accident prediction
    speed = get_estimated_speed(acc_x, acc_y)
    accident_percentage, risk_level = calculate_accident_percentage(
        acc_x, acc_y, acc_z
    )
    
    message = f"""
🚨 ALERT! 🚨

Reason: {alert_reason}

Driver is sleepy while driving!

Speed: {speed} km/h

Accident Probability: {accident_percentage}%

Risk Level: {risk_level}

Acceleration Data:
X Axis: {acc_x}
Y Axis: {acc_y}
Z Axis: {acc_z}


Location: Bhopal, MP {live_location}
Time: {current_time}

Please check immediately.
"""

    print("====================================")
    print("Sending WhatsApp Alert...")
    print(f"Reason: {alert_reason}")
    print(f"Time: {current_time}")
    print(f"Speed: {speed} km/h")
    print(f"Accident Probability: {accident_percentage}%")
    print("====================================")

    for phone_number in family_members:

        print(f"Sending to: {phone_number}")

        pywhatkit.sendwhatmsg_instantly(
            phone_number,
            message,
            wait_time=20,
            tab_close=False,
            close_time =5
        )

        time.sleep(10)

        pyautogui.click()
        time.sleep(2)


        pyautogui.press("enter")
        
        time.sleep(2)


        pyautogui.click(x=1335, y=955)

        time.sleep(2)

        print(f"Message sent to {phone_number}")

        time.sleep(8)


    print("All WhatsApp Alerts Sent Successfully!")

send_whatsapp_alert("Testing Alert System")
