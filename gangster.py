from typing import Tuple
from pathlib import Path
from imutils import face_utils
import imutils
import numpy as np
import dlib
import cv2


_rt = Path(__file__).resolve().parent


# load face and landmark detectors
face_detector = dlib.get_frontal_face_detector()
landmark_predictor = dlib.shape_predictor(
    str(_rt / "shape_predictor_68_face_landmarks.dat")
)

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

# load glasses image
glasses = cv2.imread(str(_rt / "glasses.png"), cv2.IMREAD_UNCHANGED)
gh, gw = glasses.shape[:2]
scale = 0.4
gh = int(gh * scale)
gw = int(gw * scale)
glasses = cv2.resize(glasses, (gw, gh))
glasses_mask = cv2.cvtColor(glasses[:, :, 3], cv2.COLOR_GRAY2BGR)
glasses = glasses[:, :, :3]


def make_gangster(frame: np.ndarray) -> int:
    """
    Draw gangster glasses to all faces in the frame.
    Modifies the image inplace.

    Returns the number of faces
    """
    shape_y, shape_x = frame.shape[:2]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # detect faces in the grayscale frame
    rects = face_detector(gray, 0)

    # loop over the face detections
    for rect in rects:
        # get facial landmarks for the face region
        shape = landmark_predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)
        # extract the left and right eye coordinates
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]

        # find center of eyes
        leftEyeC = np.mean(leftEye, axis=0).astype(int)
        rightEyeC = np.mean(rightEye, axis=0).astype(int)

        # find angle, distance between eyes and center between eyes
        vec = leftEyeC - rightEyeC
        theta = -np.rad2deg(np.arctan2(vec[1], vec[0]))
        dis = np.sqrt(np.mean(np.square(vec)))
        center = np.mean([leftEyeC, rightEyeC], axis=0).astype(int)

        # calculate resize scale of glasses
        scale = dis / gw
        _gw = int(4 * gw * scale)  # glasses width
        _gh = int(4 * gh * scale)  # glasses height
        _glasses = cv2.resize(glasses, (_gw, _gh))
        _glasses_mask = cv2.resize(glasses_mask, (_gw, _gh))

        # rotate glasses to eye level
        _glasses = imutils.rotate(_glasses, theta)
        _glasses_mask = imutils.rotate(_glasses_mask, theta)

        # coord on frame to place glasses
        xmin = int(center[0] - _gw / 2)
        ymin = int(center[1] - _gh / 2)
        xmax = xmin + _gw
        ymax = ymin + _gh

        # coords for glasses
        gxmin = -min(xmin, 0)
        gymin = -min(ymin, 0)
        gxmax = _gw - max(xmin + _gw - shape_x, 0)
        gymax = _gh - max(ymin + _gh - shape_y, 0)

        # calculate slices to index
        slice_y = slice(max(ymin, 0), min(ymax, shape_y))
        slice_x = slice(max(xmin, 0), min(xmax, shape_x))
        gslice_y = slice(gymin, gymax)
        gslice_x = slice(gxmin, gxmax)

        # slice glasses in case the edges are outside the frame
        _glasses = _glasses[gslice_y, gslice_x]
        _glasses_mask = _glasses_mask[gslice_y, gslice_x]

        try:
            mask = np.where(_glasses_mask < 100, frame[slice_y, slice_x], _glasses)
            frame[slice_y, slice_x] = mask
        except ValueError as e:
            print(e)

    return len(rects)
