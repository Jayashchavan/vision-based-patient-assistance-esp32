Vision-Based Patient Assistance and Emergency Alert System Using ESP32

A computer-vision-based prototype exploring hands-free patient assistance through hand gesture recognition, with local alerts and planned mobile notifications.

🎯 Project Overview

This project uses a webcam to detect hand gestures through Python, OpenCV, and MediaPipe. The detected gesture can trigger an ESP32-controlled LED and buzzer to demonstrate a patient assistance alert system.

✨ Planned Features

- ✋ Attention Request: Open-palm gesture for routine assistance.
- 🚨 Emergency Gesture: Rapid side-to-side hand wave detection.
- 🔊 Local Alerts: ESP32-controlled LED and buzzer.
- 📱 Mobile Notifications: Telegram integration planned.
- 🚁 Future Scope: Drone-assisted disaster response to help locate people in floodwater or near collapsed structures and relay location information to rescue teams.

🛠️ Technology Stack

- Python
- OpenCV
- MediaPipe Hand Landmarker
- ESP32-WROOM-32
- Arduino IDE and C++
- USB serial communication
- Telegram Bot API (planned integration)

🔄 System Architecture

Webcam → Hand Landmark Detection → Gesture Classification → Serial Communication → ESP32 → LED and B
