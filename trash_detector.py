
import os
import sys


TRASH = [
    'bottle',
    'cup',
    'fork',
    'knife',
    'spoon'
    'banana',
    'apple',
    'sandwich',
    'orange',
    'broccoli',
    'carrot',
    'hot dog',
    'pizza',
    'donut',
    'cake'
]


YOLO_PATH = os.path.join(sys.path[0], 'yc')
IMAGE_PATH = os.path.join(sys.path[0], 'input.jpg')
DEFAULT_CONFIDENCE = 0.5
DEFAULT_THRESHOLD = 0.3


import numpy as np
import argparse
import time
import cv2

labelsPath = os.path.join(YOLO_PATH, 'coco.names')
LABELS = open(labelsPath).read().strip().splitlines()

# random list of colors for class labels
np.random.seed(42)
COLORS = np.random.randint(0, 255, size=(len(LABELS), 3), dtype='uint8')

weightsPath = os.path.join(YOLO_PATH, 'yolov3.weights')
configPath = os.path.join(YOLO_PATH, 'yolov3.cfg')

# load YOLO data
net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)


def process_image(image):
    (H, W) = image.shape[:2]

    # determine only the *output* layer names that we need from YOLO
    ln = net.getLayerNames()
    ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    # construct blob from image
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    end = time.time()

    # show timing information on YOLO
    print('took {:.6f} seconds'.format(end - start))

    boxes = []
    confidences = []
    classIDs = []

    for output in layerOutputs:
        for detection in output:
            # extract the class ID and confidence (i.e., probability) of
            # the current object detection
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            if confidence < DEFAULT_CONFIDENCE:
                continue

            # scale the bounding box coordinates back
            box = detection[0:4] * np.array([W, H, W, H])
            (centerX, centerY, width, height) = box.astype('int')
            x = int(centerX - (width / 2))
            y = int(centerY - (height / 2))
            boxes.append([x, y, int(width), int(height)])
            confidences.append(float(confidence))
            classIDs.append(classID)

    # apply non-maxima suppression to suppress weak, overlapping bounding
    # boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, DEFAULT_CONFIDENCE, DEFAULT_THRESHOLD)

    # ensure at least one detection exists
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            label = LABELS[classIDs[i]]
            if label not in TRASH:
                continue

            # extract the bounding box coordinates
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            # draw a bounding box rectangle and label on the image
            color = [int(c) for c in COLORS[classIDs[i]]]
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
            text = LABELS[classIDs[i]]
            cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, color, 2)

    return image
