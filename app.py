from flask import Flask, redirect, url_for, request, render_template

import os
import cv2
import math
import argparse


from werkzeug.utils import secure_filename

app = Flask(__name__)


def highlightFace(net, frame, conf_threshold=0.7):
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]
    frameWidth = frameOpencvDnn.shape[1]
    blob = cv2.dnn.blobFromImage(
        frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False
    )

    net.setInput(blob)
    detections = net.forward()
    faceBoxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            faceBoxes.append([x1, y1, x2, y2])
            cv2.rectangle(
                frameOpencvDnn,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                int(round(frameHeight / 150)),
                8,
            )
    return frameOpencvDnn, faceBoxes


faceProto = "opencv_face_detector.pbtxt"
faceModel = "opencv_face_detector_uint8.pb"
ageProto = "age_deploy.prototxt"
ageModel = "age_net.caffemodel"
genderProto = "gender_deploy.prototxt"
genderModel = "gender_net.caffemodel"

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
ageList = [
    "(0-2)",
    "(4-6)",
    "(8-12)",
    "(15-20)",
    "(25-32)",
    "(38-43)",
    "(48-53)",
    "(60-100)",
]
genderList = ["Male", "Female"]

faceNet = cv2.dnn.readNet(faceModel, faceProto)
ageNet = cv2.dnn.readNet(ageModel, ageProto)
genderNet = cv2.dnn.readNet(genderModel, genderProto)


@app.route("/", methods=["GET"])
def index():
    # Main page
    return render_template("index.html")


@app.route("/predict", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        # Get the file from post request
        f = request.files["file"]

        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(basepath, "uploads", secure_filename(f.filename))
        f.save(file_path)

        # Make prediction
        video = cv2.VideoCapture(file_path)
        padding = 20
        while cv2.waitKey(1) < 0:
            hasFrame, frame = video.read()
            if not hasFrame:
                cv2.waitKey()
                break
            resultImg, faceBoxes = highlightFace(faceNet, frame)
            if not faceBoxes:
                # print("No face detected")
                return "No face detected"
            else:
                for faceBox in faceBoxes:
                    face = frame[
                        max(0, faceBox[1] - padding) : min(
                            faceBox[3] + padding, frame.shape[0] - 1
                        ),
                        max(0, faceBox[0] - padding) : min(
                            faceBox[2] + padding, frame.shape[1] - 1
                        ),
                    ]
                    blob = cv2.dnn.blobFromImage(
                        face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False
                    )
                    genderNet.setInput(blob)
                    genderPreds = genderNet.forward()
                    gender = genderList[genderPreds[0].argmax()]
                    # print(f'Gender: {gender}')
                    ageNet.setInput(blob)
                    agePreds = ageNet.forward()
                    age = ageList[agePreds[0].argmax()]
                    # print(f'Age: {age[1:-1]} years')
                    show1 = str("Gender - " + gender + ", Age - " + age)
                    return show1  # ,str(class_list[0][1])
    return None


if __name__ == "__main__":
    app.run()
