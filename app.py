# app.py (FIX HISTORY NOT SHOWING)
# app.py
# ADD THIS IMPORTS AT TOP
from flask import Flask, render_template, jsonify, Response
import json
import os
import cv2
import os
os.makedirs("static", exist_ok=True)
from flask import send_file
from reportlab.pdfgen import canvas
import io
import json

app = Flask(__name__)

DATA_FILE = "crowd_data.json"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/data")
def data():

    if not os.path.exists(DATA_FILE):
        return jsonify({
            "cam1":{"count":0,"alert":"Normal","mode":"Safe"},
            "cam2":{"count":0,"alert":"Normal","mode":"Safe"},
            "reds":0,
            "oranges":0,
            "labels1":[],
            "counts1":[],
            "labels2":[],
            "counts2":[],
            "history":[]
        })

    with open(DATA_FILE, "r") as f:
        info = json.load(f)

    return jsonify(info)

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
vid = cv2.VideoCapture("66.mp4")


def gen_frames(camera):

    while True:

        success, frame = camera.read()

        if not success:
            camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route("/video_feed1")
def video_feed1():
    return Response(
        gen_frames(cam),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route("/video_feed2")
def video_feed2():
    return Response(
        gen_frames(vid),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route("/download-report")
def download_report():

    import matplotlib.pyplot as plt
    from reportlab.lib.utils import ImageReader

    with open("crowd_data.json", "r") as f:
        data = json.load(f)

    # Graph create
    plt.figure(figsize=(8,4))
    plt.plot(data["labels1"], data["counts1"], marker='o', label="Camera 1")
    plt.plot(data["labels2"], data["counts2"], marker='o', label="Camera 2")
    plt.title("Crowd Trend Report")
    plt.xlabel("Time")
    plt.ylabel("People Count")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    graph_path = "report_graph.png"
    plt.savefig(graph_path)
    plt.close()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.setTitle("Crowd Monitoring Report")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(150, 800, "AI Crowd Monitoring Report")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 770, f"Red Alerts: {data['reds']}")
    pdf.drawString(250, 770, f"Orange Alerts: {data['oranges']}")

    # Insert graph
    pdf.drawImage(ImageReader(graph_path), 40, 470, width=520, height=250)

    # History
    pdf.drawString(50, 440, "Recent Detection History:")

    y = 420

    for row in data["history"][:10]:

        line = f"{row['camera']} | {row['count']} | {row['alert']} | {row['time']}"
        pdf.drawString(50, y, line)

        y -= 18

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Crowd_Report.pdf",
        mimetype="application/pdf"
    )

    with open("crowd_data.json", "r") as f:
        data = json.load(f)

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.setTitle("Crowd Monitoring Report")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(160, 800, "Crowd Monitoring Report")

    pdf.setFont("Helvetica", 12)

    pdf.drawString(50, 760, f"Total Red Alerts: {data['reds']}")
    pdf.drawString(50, 740, f"Total Orange Alerts: {data['oranges']}")

    pdf.drawString(50, 710, "Recent Detection History:")

    y = 690

    for row in data["history"][:15]:

        line = f"{row['camera']} | Count:{row['count']} | {row['alert']} | {row['time']}"
        pdf.drawString(50, y, line)

        y -= 20

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Crowd_Report.pdf",
        mimetype="application/pdf"
    )
if __name__ == "__main__":
    app.run(debug=True)