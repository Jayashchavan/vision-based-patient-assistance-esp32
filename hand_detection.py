import cv2
import mediapipe as mp

model_path = "hand_landmarker.task"

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=RunningMode.VIDEO,
    num_hands=1
)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Could not open webcam")
    raise SystemExit

print("Hand detection started. Press Q to quit.")

timestamp = 0

with HandLandmarker.create_from_options(options) as detector:
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Could not read webcam frame")
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        timestamp += 33
        result = detector.detect_for_video(image, timestamp)

        if result.hand_landmarks:
            for hand in result.hand_landmarks:
                for point in hand:
                    x = int(point.x * frame.shape[1])
                    y = int(point.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

                connections = [
                    (0, 1), (1, 2), (2, 3), (3, 4),
                    (0, 5), (5, 6), (6, 7), (7, 8),
                    (5, 9), (9, 10), (10, 11), (11, 12),
                    (9, 13), (13, 14), (14, 15), (15, 16),
                    (13, 17), (17, 18), (18, 19), (19, 20),
                    (0, 17)
                ]

                for start, end in connections:
                    x1 = int(hand[start].x * frame.shape[1])
                    y1 = int(hand[start].y * frame.shape[0])
                    x2 = int(hand[end].x * frame.shape[1])
                    y2 = int(hand[end].y * frame.shape[0])

                    cv2.line(
                        frame, (x1, y1), (x2, y2),
                        (0, 255, 0), 2
                    )

                cv2.putText(
                    frame, "Hand Detected",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2
                )

        cv2.imshow("AI Hand Detection - Press Q to Quit", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()