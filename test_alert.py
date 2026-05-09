import pywhatkit
import datetime

def test_whatsapp_alert():
    phone_number = "+919691451796"   # Replace with your family member number

    message = """
TEST ALERT 🚗

Driver sleep detection system is working!

Current Speed: 62 km/hr
Location: Bhopal, MP

Please check immediately.
"""

    now = datetime.datetime.now()

    hour = now.hour
    minute = now.minute + 2   # message sends after 2 minutes

    # handle if minute becomes > 59
    if minute >= 60:
        hour += 1
        minute = minute - 60

    print("Scheduling WhatsApp message...")
    print(f"Sending to: {phone_number}")
    print(f"Time: {hour}:{minute}")

    pywhatkit.sendwhatmsg(
        phone_number,
        message,
        hour,
        minute,
        wait_time=10,
        tab_close=True,
        close_time=5
    )

    print("Message scheduled successfully!")

# Run test
test_whatsapp_alert()