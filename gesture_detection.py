import cv2
import mediapipe as mp

model_path = "hand_landmarker.task"

options = mp.tasks.vision.HandLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(
        model_asset_path=model_path
    ),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_hands=1
)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Could not open webcam")
    raise SystemExit

timestamp = 0
last_gesture = "No hand detected"

def classify_hand(hand):
    # Landmark indices for fingertips and their
    # corresponding finger joints.
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]

    # For each finger, compare fingertip height
    # with the middle joint. Image y decreases upward.
    extended = sum(
        hand[tip].y < hand[joint].y
        for tip, joint in zip(tips, pips)
    )

    # Thumb is treated separately.
    thumb_extended = abs(hand[4].x - hand[2].x) > 0.08

    if extended >= 3 and thumb_extended:
        return "OPEN PALM"

    if extended <= 1 and not thumb_extended:
        return "CLOSED FIST"

    return "OTHER GESTURE"

with mp.tasks.vision.HandLandmarker.create_from_options(
    options
) as detector:

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        timestamp += 33
        result = detector.detect_for_video(image, timestamp)

        gesture = "No hand detected"

        if result.hand_landmarks:
            hand = result.hand_landmarks[0]
            gesture = classify_hand(hand)

            for point in hand:
                x = int(point.x * frame.shape[1])
                y = int(point.y * frame.shape[0])
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

        cv2.putText(
            frame,
            gesture,
            (20, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.imshow("Gesture Recognition - Press Q to Quit", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()