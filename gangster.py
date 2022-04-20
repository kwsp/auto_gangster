from imutils import face_utils
import imutils
import numpy as np
import dlib
import cv2


# load face and landmark detectors
face_detector = dlib.get_frontal_face_detector()
landmark_predictor = dlib.shape_predictor("./shape_predictor_68_face_landmarks.dat")

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

# load glasses image
glasses = cv2.imread("./glasses.png", cv2.IMREAD_UNCHANGED)
gh, gw = glasses.shape[:2]
scale = 0.4
gh = int(gh * scale)
gw = int(gw * scale)
glasses = cv2.resize(glasses, (gw, gh))
glasses_mask = cv2.cvtColor(glasses[:, :, 3], cv2.COLOR_GRAY2BGR)
glasses = glasses[:, :, :3]


def make_gangster(frame: np.ndarray) -> np.ndarray:
    """
    Draw gangster glasses to all faces in the frame
    """

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # detect faces in the grayscale frame
    rects = face_detector(gray, 0)

    # loop over the face detections
    for rect in rects:
        # determine the facial landmarks for the face region, then
        # convert the facial landmark (x, y)-coordinates to a NumPy
        # array
        shape = landmark_predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)
        # extract the left and right eye coordinates, then use the
        # coordinates to compute the eye aspect ratio for both eyes
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]

        # # compute the convex hull for the left and right eye, then
        # # visualize each of the eyes
        # leftEyeHull = cv2.convexHull(leftEye)
        # rightEyeHull = cv2.convexHull(rightEye)
        # cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
        # cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

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
        _gw = int(4*gw * scale)
        _gh = int(4*gh * scale)
        # print(f"{_gw=} {_gh=}")
        _glasses = cv2.resize(glasses, (_gw, _gh))
        _glasses_mask = cv2.resize(glasses_mask, (_gw, _gh))

        # rotate glasses
        _glasses = imutils.rotate(_glasses, theta)
        _glasses_mask = imutils.rotate(_glasses_mask, theta)

        x = int(center[0] - _gw/2)
        y = int(center[1] - _gh/2)
        slice_y = slice(y, y+_gh)
        slice_x = slice(x, x+_gw)
        try:
            mask = np.where(_glasses_mask < 100, frame[slice_y, slice_x], _glasses)
            frame[slice_y, slice_x] = mask
        except ValueError:
            # TODO: fix this
            print("Glasses out of bounds")

    return frame
