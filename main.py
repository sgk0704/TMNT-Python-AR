from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit
import cv2
import os
import cvzone
from cvzone.PoseModule import PoseDetector

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

def gen_frames():
    camera = cv2.VideoCapture(0)
    desired_width = 1280
    desired_height = 720

    detector = PoseDetector()

    shirtFolderPath = "Resources/Shirts"
    listShirts = os.listdir(shirtFolderPath)
    fixedRatio = 292 / 200  # widthOfShirt/widthOfPoint11to12
    shirtRatioHeightWidth = 631 / 680
    imageNumber = 0
    imgButtonRight = cv2.imread("Resources/button.png", cv2.IMREAD_UNCHANGED)
    imgButtonLeft = cv2.flip(imgButtonRight, 1)
    counterRight = 0
    counterLeft = 0
    selectionSpeed = 10

    while True:
        ret, imgsize = camera.read()
        img = cv2.resize(imgsize, (desired_width, desired_height))
        img = detector.findPose(img)

        lmList, bboxInfo = detector.findPosition(img, bboxWithHands=False, draw=False)
        if lmList:
            lm11 = lmList[11][1:3]
            lm12 = lmList[12][1:3]
            imgShirt = cv2.imread(os.path.join(shirtFolderPath, listShirts[imageNumber]), cv2.IMREAD_UNCHANGED)
            
            widthOfShirt = int((lm11[0] - lm12[0]) * fixedRatio)
            imgShirt = cv2.resize(imgShirt, (widthOfShirt, int(widthOfShirt * shirtRatioHeightWidth)))
            currentScale = (lm11[0] - lm12[0]) / 190
            offset = int(44 * currentScale), int(48 * currentScale)

            try:
                img = cvzone.overlayPNG(img, imgShirt, (lm12[0] - offset[0], lm12[1] - offset[1]))
            except Exception as e:
                pass
                # Handle overlaying error

            img = cvzone.overlayPNG(img, imgButtonRight, (1074, 293))
            img = cvzone.overlayPNG(img, imgButtonLeft, (72, 293))

            if lmList[16][1] < 300:
                counterRight += 1
                cv2.ellipse(img, (139, 360), (66, 66), 0, 0, counterRight * selectionSpeed, (0, 255, 0), 20)
                if counterRight * selectionSpeed > 360:
                    counterRight = 0
                    if imageNumber < len(listShirts) - 1:
                        imageNumber += 1
            elif lmList[15][1] > 900:
                counterLeft += 1
                cv2.ellipse(img, (1138, 360), (66, 66), 0, 0, counterLeft * selectionSpeed, (0, 255, 0), 20)
                if counterLeft * selectionSpeed > 360:
                    counterLeft = 0
                    if imageNumber > 0:
                        imageNumber -= 1
            else:
                counterRight = 0
                counterLeft = 0

        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


    camera.release()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect', namespace='/video_socket')
def test_connect():
    print('Client connected')

@socketio.on('disconnect', namespace='/video_socket')
def test_disconnect():
    print('Client disconnected')

@socketio.on('frame', namespace='/video_socket')
def handle_frame(frame):
    # Process the frame as needed (if required)
    # You can add more processing here...

    # Send the processed frame back to the client (if needed)
    emit('processed_frame', frame, namespace='/video_socket', broadcast=True)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    socketio.run(app, debug=True)
