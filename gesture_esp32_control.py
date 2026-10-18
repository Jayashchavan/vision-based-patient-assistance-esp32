import cv2
import mediapipe as mp
import serial
import time
import requests
from collections import deque

# ---------------- ESP32 CONFIGURATION ----------------
PORT = "COM11"
BAUD_RATE = 115200
MODEL_PATH = "hand_landmarker.task"

# ---------------- TELEGRAM CONFIGURATION ----------------
BOT_TOKEN = "PASTE_YOUR_NEW_BOT_TOKEN_HERE"
CHAT_ID = "8127873527"

# ---------------- GESTURE SETTINGS ----------------
WAVE_WINDOW = 1.0
MIN_WAVE_RANGE = 0.12
MIN_REVERSALS = 2
MIN_STEP = 0.025
WAVE_COOLDOWN = 3.0

ATTENTION_HOLD = 0.8
HAND_LOST_RESET = 0.6

history = deque()
last_wave_time = 0.0
open_palm_since = None
last_seen_time = None
attention_sent = False
emergency_latched = False
waiting_for_release = False


def classify_hand(hand):
    tips = [8, 12, 16, 20]
    joints = [6, 10, 14, 18]

    extended = sum(
        hand[tip].y < hand[joint].y
        for tip, joint in zip(tips, joints)
    )
    thumb_extended = abs(hand[4].x - hand[2].x) > 0.08

    if extended >= 3 and thumb_extended:
        return "OPEN PALM"
    if extended <= 1 and not thumb_extended:
        return "CLOSED FIST"
    return "OTHER GESTURE"


def count_reversals(values):
    reversals = 0
    previous_direction = 0

    for index in range(1, len(values)):
        delta = values[index] - values[index - 1]

        if abs(delta) < MIN_STEP:
            continue

        direction = 1 if delta > 0 else -1

        if previous_direction and direction != previous_direction:
            reversals += 1

        previous_direction = direction

    return reversals


def send_telegram_alert(message):
    if BOT_TOKEN == "PASTE_YOUR_NEW_BOT_TOKEN_HERE":
        print("Telegram is not configured: add your new bot token.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            json={"chat_id": CHAT_ID, "text": message},
            timeout=3
        )
        response.raise_for_status()

        if response.json().get("ok"):
            print("Telegram alert sent successfully!")
        else:
            print("Telegram did not confirm the alert.")

    except requests.RequestException as error:
        print(f"Telegram alert failed: {error}")


def send_command(esp32, command):
    esp32.write((command + "\n").encode("utf-8"))
    esp32.flush()
    print(f"Sent to ESP32: {command}")


# ---------------- CONNECT TO ESP32 ----------------
try:
    esp32 = serial.Serial(PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    esp32.reset_input_buffer()
    print(f"Connected to ESP32 on {PORT}")

except serial.SerialException as error:
    print(f"ESP32 connection failed: {error}")
    raise SystemExit(1)


# ---------------- OPEN WEBCAM ----------------
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Could not open webcam.")
    esp32.close()
    raise SystemExit(1)


# ---------------- MEDIAPIPE CONFIGURATION ----------------
options = mp.tasks.vision.HandLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(
        model_asset_path=MODEL_PATH
    ),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_hands=1
)


# ---------------- MAIN GESTURE LOOP ----------------
try:
    with mp.tasks.vision.HandLandmarker.create_from_options(
        options
    ) as detector:

        print("Open palm -> ATTENTION: 2 beeps + Telegram")
        print("Whole-hand wave -> EMERGENCY: 8 beeps + Telegram")
        print("Press C to clear; Q to quit")

        timestamp_ms = 0

        while True:
            ok, frame = cap.read()

            if not ok:
                print("Could not read webcam frame.")
                break

            now = time.monotonic()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb
            )

            timestamp_ms += 33
            result = detector.detect_for_video(
                mp_image, timestamp_ms
            )

            gesture = "NO HAND DETECTED"
            label = gesture
            command = None

            if result.hand_landmarks:
                hand = result.hand_landmarks[0]
                last_seen_time = now
                gesture = classify_hand(hand)
                label = gesture

                # Track the palm's horizontal position.
                palm_x = sum(
                    hand[index].x for index in [0, 5, 9, 13, 17]
                ) / 5

                history.append((now, palm_x))

                while history and now - history[0][0] > WAVE_WINDOW:
                    history.popleft()

                xs = [sample[1] for sample in history]

                x_range = (
                    max(xs) - min(xs)
                    if len(xs) >= 3
                    else 0
                )
                reversals = count_reversals(xs)

                waving = (
                    len(xs) >= 4
                    and x_range >= MIN_WAVE_RANGE
                    and reversals >= MIN_REVERSALS
                )

                # Emergency wave takes priority.
                if (
                    waving
                    and not emergency_latched
                    and not waiting_for_release
                    and now - last_wave_time >= WAVE_COOLDOWN
                ):
                    command = "EMERGENCY"
                    label = "EMERGENCY WAVE"

                    emergency_latched = True
                    last_wave_time = now
                    open_palm_since = None
                    history.clear()

                elif (
                    gesture == "OPEN PALM"
                    and not waving
                    and not emergency_latched
                    and not waiting_for_release
                ):
                    if open_palm_since is None:
                        open_palm_since = now

                    if (
                        now - open_palm_since >= ATTENTION_HOLD
                        and not attention_sent
                    ):
                        command = "ATTENTION"
                        attention_sent = True
                        label = "OPEN PALM - ATTENTION"

                else:
                    open_palm_since = None

                # Draw detected hand landmarks.
                for point in hand:
                    px = int(point.x * frame.shape[1])
                    py = int(point.y * frame.shape[0])
                    cv2.circle(
                        frame, (px, py), 4, (0, 255, 0), -1
                    )

                cv2.putText(
                    frame,
                    f"X range: {x_range:.3f}  Reversals: {reversals}",
                    (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 0),
                    2
                )

            else:
                history.clear()
                open_palm_since = None

                if last_seen_time is None:
                    last_seen_time = now

                if now - last_seen_time >= HAND_LOST_RESET:
                    attention_sent = False
                    waiting_for_release = False

            if emergency_latched:
                label = "EMERGENCY ACTIVE - Press C to clear"
            elif waiting_for_release:
                label = "CLEARED - Remove hand to rearm"

            # Send one ESP32 command and one Telegram message per event.
            if command:
                send_command(esp32, command)

                if command == "ATTENTION":
                    send_telegram_alert(
                        "🟡 WINSTON - ATTENTION ALERT\n"
                        "Patient may need assistance. Please check on them."
                    )

                elif command == "EMERGENCY":
                    send_telegram_alert(
                        "🚨 WINSTON - EMERGENCY ALERT\n"
                        "Patient needs urgent assistance. Please check immediately."
                    )

            cv2.putText(
                frame,
                label,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

            cv2.imshow(
                "Patient Assistance - C: Clear, Q: Quit",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("c"):
                send_command(esp32, "CLEAR")
                emergency_latched = False
                attention_sent = False
                open_palm_since = None
                history.clear()
                waiting_for_release = True
                last_seen_time = now

            elif key == ord("q"):
                break

finally:
    cap.release()
    cv2.destroyAllWindows()

    if esp32.is_open:
        esp32.close()

    print("Webcam and ESP32 connection closed.")