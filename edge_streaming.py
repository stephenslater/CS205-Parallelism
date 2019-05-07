import os
import tensorflow as tf
import numpy as np
from matplotlib import pyplot as plt
import time
import tqdm
import numpy as np
from pathlib import Path
import argparse
from PIL import Image
import cv2
import copy
import mss

sess = tf.Session()
graph = tf.get_default_graph()

MODEL_PATH = os.path.join(os.environ['HOME'], "models")

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', dest='model', type=str,
                    default='faster_rcnn_resnet101_coco_2018_01_28',
                    help="Name of model in model folder")
args = parser.parse_args()


CV_MODEL = args.model
saver = tf.train.import_meta_graph(os.path.join(MODEL_PATH, CV_MODEL, 'model.ckpt.meta'))
saver.restore(sess, tf.train.latest_checkpoint(os.path.join(MODEL_PATH, CV_MODEL)))

input_tensor = graph.get_tensor_by_name('image_tensor:0')
output_tensors = dict(
    bboxes = graph.get_tensor_by_name('detection_boxes:0'),
    classes = graph.get_tensor_by_name('detection_classes:0'),
    n = graph.get_tensor_by_name('num_detections:0'),
    scores = graph.get_tensor_by_name('detection_scores:0'),
)

SCALING = 1.2
monitor = {'top': 160,
           'left': 160,
           'width': int(640 * SCALING),
           'height': int(360 * SCALING)}
sct = mss.mss()
while True:
    last_time = time.time()
    grabbed_image = sct.grab(monitor)
    image = np.array(grabbed_image)
    # Need to convert BGRA to BGR
    image = image[:,:,:3]

    # Run this image through the ML model.
    frame = np.expand_dims(image, 0)
    output = sess.run(output_tensors, feed_dict={input_tensor: frame})
    bboxes, scores, classes = output['bboxes'], output['scores'], output['classes']

    # Filter for high scores.
    indices = scores > 0.3
    bboxes = bboxes[indices]
    scores = scores[indices]
    classes = classes[indices]

    # Make a copy of the image for displaying.
    display_image = image[:]
    display = np.array(image[:])
    # Scale the bounding boxes to the image size.
    h, w, _ = image.shape
    bboxes *= np.array([h, w, h, w])
    num_dets = len(bboxes)
    if num_dets > 0:
        centers_y = bboxes[:, [0, 2]].mean(axis=1)
        centers_x = bboxes[:, [1, 3]].mean(axis=1)
        for i in range(num_dets):
            cx, cy = centers_x[i], centers_y[i]
            color = (0, 255, 0) if classes[i] == 1 else (0, 0, 255)
            cv2.circle(display, (cx, cy), 5, color, -1)
    
    msg = "Number of people: {}".format(num_dets)
    vel_msg = "Average Velocity: {}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontcolor = (0, 0, 0)
    fontscale = 1
    cv2.putText(display, msg, (10, 420), font, fontscale, fontcolor, 2, cv2.LINE_AA)
    cv2.putText(display, vel_msg, (10, 380), font, fontscale, fontcolor, 2, cv2.LINE_AA)
    
    cv2.imshow("Science Center Plaza Stream", display)
    print("fps: {}".format(1 / (time.time() - last_time)))
    
    # Press "q" to quit
    if cv2.waitKey(25) & 0xFF == ord("q"):
        cv2.destroyAllWindows()
        break