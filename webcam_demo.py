# import the necessary packages
from imutils.video import VideoStream
import imutils
import time
import cv2

from gangster import make_gangster


print("[INFO] starting video stream thread...")

vs = VideoStream(src=0).start()
time.sleep(1.0)
# loop over frames from the video stream
while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=550)

    n = make_gangster(frame)

    # fmt: off
    cv2.putText(frame, f"# faces: {n}", (10, 30),
        cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 0), 1, cv2.LINE_AA)

    # show the frame
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break

cv2.destroyAllWindows()
vs.stop()
