import cv2
import gangster

img = cv2.imread("input.jpg")
gangster.make_gangster(img)
cv2.imwrite("output.jpg", img)
