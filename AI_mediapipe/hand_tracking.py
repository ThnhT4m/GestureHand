import cv2
import time
import os
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import socket
import json

# --- ESP32 ---
ESP32_IP   = 'YOUR IP'
ESP32_PORT = 4210
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- Mapping ngón tay ---
FINGERS = {
    "thumb":   (4,  2),
    "index":   (8,  6),
    "middle":  (12, 10),
    "ring":    (16, 14),
    "pinky":   (20, 18),
}

SERVO_DIRECTION = {
    "thumb":  1,
    "index":  1,
    "middle": 1,
    "ring":   1,
    "pinky":  1
}

def is_finger_up(lm, tip_id, pip_id, name, direction):
    if name == "thumb":
        return lm[4].x < lm[2].x if direction == "FRONT" else lm[4].x > lm[2].x
    else:
        return lm[tip_id].y < lm[pip_id].y

def get_hand_direction(world_lm):
    wrist     = np.array([world_lm[0].x,  world_lm[0].y,  world_lm[0].z])
    index_mcp = np.array([world_lm[5].x,  world_lm[5].y,  world_lm[5].z])
    pinky_mcp = np.array([world_lm[17].x, world_lm[17].y, world_lm[17].z])
    v1 = index_mcp - wrist
    v2 = pinky_mcp - wrist
    normal = np.cross(v1, v2)
    return "FRONT" if normal[2] > 0 else "BACK"

def get_wrist_rotation(world_lm):
    wrist      = np.array([world_lm[0].x,  world_lm[0].y,  world_lm[0].z])
    middle_mcp = np.array([world_lm[9].x,  world_lm[9].y,  world_lm[9].z])
    index_mcp  = np.array([world_lm[5].x,  world_lm[5].y,  world_lm[5].z])
    pinky_mcp  = np.array([world_lm[17].x, world_lm[17].y, world_lm[17].z])

    # Vector ngang bàn tay (index → pinky)
    side = pinky_mcp - index_mcp
    # Vector dọc bàn tay (wrist → middle)
    forward = middle_mcp - wrist

    # Normal của mặt phẳng bàn tay
    normal = np.cross(forward, side)
    normal = normal / (np.linalg.norm(normal) + 1e-6)

    # Góc nghiêng theo trục Z (xoay trước/sau)
    angle = np.degrees(np.arcsin(np.clip(normal[2], -1, 1)))
    return angle  # -90 đến +90

def process_and_send(frame, lm, world_lm):
    direction = get_hand_direction(world_lm)

    cv2.putText(frame, f"Direction: {direction}", (10, 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 2)

    servo_data = {}



    # ===== 5 NGÓN =====
    for i, (name, (tip, pip)) in enumerate(FINGERS.items()):
        up = is_finger_up(lm, tip, pip, name, direction)
        base_angle = 180 if up else 0
        angle = base_angle if SERVO_DIRECTION[name] == 1 else 180 - base_angle

        if name == "thumb":
            servo_data["thumb1"] = angle
            servo_data["thumb2"] = angle
            text = f"thumb: {'UP' if up else 'DOWN'} ({angle})"
        else:
            servo_data[name] = angle
            text = f"{name}: {'UP' if up else 'DOWN'} ({angle})"

        color = (0, 255, 0) if up else (0, 0, 255)
        cv2.putText(frame, text, (10, 40 + i * 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    payload = json.dumps(servo_data)
    sock.sendto(payload.encode(), (ESP32_IP, ESP32_PORT))

# --- MediaPipe ---
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'hand_landmarker.task')

BaseOptions        = mp.tasks.BaseOptions
HandLandmarker     = vision.HandLandmarker
HandLandmarkerOpts = vision.HandLandmarkerOptions
VisionRunningMode  = vision.RunningMode

latest_result = None

def save_result(result, output_image, timestamp_ms):
    global latest_result
    latest_result = result

options = HandLandmarkerOpts(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.LIVE_STREAM,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5,
    result_callback=save_result
)

cap = cv2.VideoCapture(0)

with HandLandmarker.create_from_options(options) as landmarker:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        landmarker.detect_async(mp_image, int(time.time() * 1000))

        right_index = None

        if latest_result and latest_result.hand_landmarks:
            for i, handedness_list in enumerate(latest_result.handedness):
                label = handedness_list[0].display_name
                if label == "Left":
                    right_index = i
                    break

        if right_index is not None:
            lm       = latest_result.hand_landmarks[right_index]
            world_lm = latest_result.hand_world_landmarks[right_index]
            process_and_send(frame, lm, world_lm)
        else:
            cv2.putText(frame, "Right hand not detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

        cv2.imshow("Hand Tracking Servo - Right Hand Only", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
sock.close()
cv2.destroyAllWindows()
