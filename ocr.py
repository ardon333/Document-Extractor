import cv2
import numpy as np

# Function to attempt to detect text-like regions and blur them
def blur_text_areas(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edged = cv2.Canny(gray, 30, 200)
    thresh = cv2.threshold(edged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Blur detected regions
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        frame[y:y+h, x:x+w] = cv2.GaussianBlur(frame[y:y+h, x:x+w], (15, 15), 0)

    return frame

# Start video capture
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Process the frame
    processed_frame = blur_text_areas(frame)

    # Display the resulting frame
    cv2.imshow('Frame', processed_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture
cap.release()
cv2.destroyAllWindows()
