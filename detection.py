# detection.py
# FINAL VERSION USING YOUR CODE
# YOLO + CSRNet + MongoDB + Dashboard History + Twilio Alert

import cv2
import time
from ultralytics import YOLO
from csrnet import csr_count
from database import alerts
from twilio.rest import Client
import json
import os

# ----------------------------
# Dashboard JSON file
# ----------------------------
DATA_FILE = "crowd_data.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({
            "cam1":{"count":0,"alert":"Normal","mode":"YOLO"},
            "cam2":{"count":0,"alert":"Normal","mode":"YOLO"},
            "reds":0,
            "oranges":0,
            "labels1":[],
            "counts1":[],
            "labels2":[],
            "counts2":[],
            "history":[]
        }, f, indent=4)

# ----------------------------
# Load YOLO
# ----------------------------
model = YOLO("models/yolov8n.pt")

# ----------------------------
# Camera Sources
# ----------------------------
cam = cv2.VideoCapture(0)
vid1 = cv2.VideoCapture("Video2.mp4")

last_save = 0

# ----------------------------
# TWILIO ALERT
# ----------------------------

account_sid = "AC916c9ea11acd57ac68f55fa813883313"
auth_token = "44238a56a6c734c69812d7e3211a64ba"

client_twilio = Client(account_sid, auth_token)

twilio_number = "+16616057315"
your_number = "+918073600976"

last_alert_time = 0


# ----------------------------
# Send Alert
# ----------------------------
def send_alert(message):

    global last_alert_time

    # Prevent spam alerts
    if time.time() - last_alert_time < 60:
        return

    try:

        client_twilio.messages.create(
            body=message,
            from_=twilio_number,
            to=your_number
        )

        print("Twilio Alert Sent")

        last_alert_time = time.time()

    except Exception as e:
        print("Twilio Error:", e)


# ----------------------------
# Detect People
# ----------------------------
def detect_people(frame):

    results = model(frame, verbose=False)

    yolo_people = 0

    for r in results:
        for box in r.boxes:

            cls = int(box.cls[0])

            if cls == 0:

                yolo_people += 1

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0,255,0),
                    2
                )

                cv2.putText(
                    frame,
                    "Person",
                    (x1, y1-8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0,255,0),
                    2
                )

    # Hybrid logic
    if yolo_people < 13:
        count = yolo_people
        mode = "YOLO"
    else:
        count = csr_count(frame)
        mode = "CSRNET"

    # Alert Logic
    if count < 5:
        alert = "GREEN"

    elif count < 13:
        alert = "ORANGE"

    else:
        alert = "RED"

        send_alert(
            f"RED ALERT! Crowd Count = {count}"
        )

    return count, mode, alert


# ----------------------------
# MAIN LOOP
# ----------------------------
while True:

    r1, frame1 = cam.read()
    r2, frame2 = vid1.read()

    if not r1:
        continue

    if not r2:
        vid1.set(cv2.CAP_PROP_POS_FRAMES, 0)
        r2, frame2 = vid1.read()

    count1, mode1, alert1 = detect_people(frame1)
    count2, mode2, alert2 = detect_people(frame2)

    now = time.strftime("%H:%M:%S")

    # Overlay
    cv2.putText(frame1, f"Count: {count1}", (20,40),
                cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)

    cv2.putText(frame1, f"Mode: {mode1}", (20,80),
                cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,0),2)

    cv2.putText(frame1, f"Alert: {alert1}", (20,120),
                cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)

    cv2.putText(frame2, f"Count: {count2}", (20,40),
                cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)

    cv2.putText(frame2, f"Mode: {mode2}", (20,80),
                cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,0),2)

    cv2.putText(frame2, f"Alert: {alert2}", (20,120),
                cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)

    # ----------------------------
    # Save every 3 sec
    # ----------------------------
    if time.time() - last_save > 3:

        # MongoDB history
        alerts.insert_one({
            "camera":"Cam1",
            "time":now,
            "count":count1,
            "mode":mode1,
            "alert":alert1
        })

        alerts.insert_one({
            "camera":"Cam2",
            "time":now,
            "count":count2,
            "mode":mode2,
            "alert":alert2
        })

        # Dashboard JSON
        with open(DATA_FILE, "r") as f:
            data = json.load(f)

        data["cam1"] = {
            "count": count1,
            "alert": alert1,
            "mode": mode1
        }

        data["cam2"] = {
            "count": count2,
            "alert": alert2,
            "mode": mode2
        }

        if alert1 == "RED":
            data["reds"] += 1
        elif alert1 == "ORANGE":
            data["oranges"] += 1

        if alert2 == "RED":
            data["reds"] += 1
        elif alert2 == "ORANGE":
            data["oranges"] += 1

        data["labels1"].append(now)
        data["counts1"].append(count1)

        data["labels2"].append(now)
        data["counts2"].append(count2)

        data["labels1"] = data["labels1"][-15:]
        data["counts1"] = data["counts1"][-15:]

        data["labels2"] = data["labels2"][-15:]
        data["counts2"] = data["counts2"][-15:]

        data["history"].insert(0,{
            "camera":"Cam1",
            "count":count1,
            "mode":mode1,
            "alert":alert1,
            "time":now
        })

        data["history"].insert(0,{
            "camera":"Cam2",
            "count":count2,
            "mode":mode2,
            "alert":alert2,
            "time":now
        })

        data["history"] = data["history"][:20]

        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

        last_save = time.time()

    cv2.imshow("Webcam Feed", frame1)
    cv2.imshow("Video Feed", frame2)

    if cv2.waitKey(1) == 27:
        break

cam.release()
vid1.release()
cv2.destroyAllWindows()