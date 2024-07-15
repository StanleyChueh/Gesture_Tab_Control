import cv2
import mediapipe as mp
import websocket
import threading
import time

# 初始化MediaPipe Hands模型
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# WebSocket URL
ws_url = "ws://localhost:8000"
ws = None  # 全局变量来存储WebSocket连接

# 滑动手势检测阈值
SLIDE_THRESHOLD_X = 0.4  # 左右滑动的阈值
SLIDE_THRESHOLD_Y = 0.35  # 向上滑动的阈值，调整这个值来改变滑动敏感度
STABILITY_FRAMES = 10  # 需要在多帧内持续检测到滑动手势，调整这个值以改变稳定性要求
GESTURE_INTERVAL = 2.5  # 手勢之間的最小間隔時間（秒）

# 滑动手势计数器
slide_count_x = 0
slide_count_y = 0
last_direction = None
last_slide_time = 0

def send_message(ws, message):
    ws.send(message)

def on_open(ws_local):
    global ws
    ws = ws_local
    print("WebSocket connection opened")

def on_close(ws):
    print("WebSocket connection closed")

def on_message(ws, message):
    print(f"Received message: {message}")

def on_error(ws, error):
    print(f"Error: {error}")

def websocket_thread():
    ws_local = websocket.WebSocketApp(ws_url,
                                      on_open=on_open,
                                      on_close=on_close,
                                      on_message=on_message,
                                      on_error=on_error)
    ws_local.run_forever()

# 启动WebSocket线程
threading.Thread(target=websocket_thread).start()

# 打开摄像头
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # 将图像从BGR转换为RGB
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # 处理图像并检测手势
    results = hands.process(image)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # 获取手势坐标
            x_coords = [landmark.x for landmark in hand_landmarks.landmark]
            y_coords = [landmark.y for landmark in hand_landmarks.landmark]
            
            # 检测左右滑动手势
            slide_distance_x = max(x_coords) - min(x_coords)
            current_time = time.time()

            if slide_distance_x > SLIDE_THRESHOLD_X:
                if x_coords[0] < x_coords[-1]:  # 从左向右滑动
                    direction = "right"
                else:  # 从右向左滑动
                    direction = "left"

                if last_direction == direction and current_time - last_slide_time < GESTURE_INTERVAL:  # 确保手势在最小间隔时间内完成
                    slide_count_x += 1
                else:
                    slide_count_x = 1  # 重置计数器

                last_direction = direction
                last_slide_time = current_time

                if slide_count_x >= STABILITY_FRAMES:  # 确保手势稳定检测到多帧
                    if direction == "right":
                        print("Swipe Right Detected")
                        if ws is not None:  # 检查WebSocket连接是否已建立
                            send_message(ws, "next_tab")
                    elif direction == "left":
                        print("Swipe Left Detected")
                        if ws is not None:  # 检查WebSocket连接是否已建立
                            send_message(ws, "previous_tab")
                    
                    slide_count_x = 0  # 重置计数器

            # 检测向上滑动手势
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            index_finger_base = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]

            current_y = index_finger_tip.y
            base_y = index_finger_base.y

            # 僅當垂直距離大於閾值且水平距離小於滑動閾值時，才檢測向上滑動手勢
            if (base_y - current_y) > SLIDE_THRESHOLD_Y and slide_distance_x < SLIDE_THRESHOLD_X:
                if current_time - last_slide_time < GESTURE_INTERVAL:  # 确保手势在最小间隔时间内完成
                    slide_count_y += 1
                else:
                    slide_count_y = 1  # 重置计数器

                last_slide_time = current_time

                if slide_count_y >= STABILITY_FRAMES:  # 确保手势稳定检测到多帧
                    print("Swipe Up Detected")
                    if ws is not None:  # 检查WebSocket连接是否已建立
                        send_message(ws, "close_tab")
                    
                    slide_count_y = 0  # 重置计数器

            # 檢測掌心朝向手勢
            palm_facing_camera = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].z < hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].z

            if palm_facing_camera:
                if current_time - last_slide_time > GESTURE_INTERVAL:
                    print("Palm Facing Camera - Switch to Left Tab")
                    if ws is not None:
                        send_message(ws, "previous_tab")
                    last_slide_time = current_time
            else:
                if current_time - last_slide_time > GESTURE_INTERVAL:
                    print("Palm Facing Away from Camera - Switch to Right Tab")
                    if ws is not None:
                        send_message(ws, "next_tab")
                    last_slide_time = current_time

            # 檢測單指向上手勢
            extended_fingers = [hand_landmarks.landmark[i].y < hand_landmarks.landmark[i - 2].y for i in [mp_hands.HandLandmark.THUMB_TIP, mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_TIP, mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.PINKY_TIP]]
            if extended_fingers.count(True) == 1 and extended_fingers[1]:  # 只有食指伸直
                if current_time - last_slide_time > GESTURE_INTERVAL:
                    print("One Finger Up - Close Tab")
                    if ws is not None:
                        send_message(ws, "close_tab")
                    last_slide_time = current_time

    cv2.imshow('Hand Gesture Detection', frame)

    if cv2.waitKey(1) & 0xFF == 27:  # 按Esc键退出
        break

cap.release()
cv2.destroyAllWindows()

