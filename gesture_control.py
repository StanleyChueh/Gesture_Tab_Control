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
SLIDE_THRESHOLD = 0.3  # 调整这个值来改变滑动敏感度 0.3
STABILITY_FRAMES = 10  # 需要在多帧内持续检测到滑动手势 5

# 滑动手势计数器
slide_count = 0
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
            slide_distance = max(x_coords) - min(x_coords)
            current_time = time.time()

            if slide_distance > SLIDE_THRESHOLD:
                if x_coords[0] < x_coords[-1]:  # 从左向右滑动
                    direction = "right"
                else:  # 从右向左滑动
                    direction = "left"

                if last_direction == direction and current_time - last_slide_time < 1:  # 确保手势在1秒内完成
                    slide_count += 1
                else:
                    slide_count = 1  # 重置计数器

                last_direction = direction
                last_slide_time = current_time

                if slide_count >= STABILITY_FRAMES:  # 确保手势稳定检测到多帧
                    if direction == "right":
                        print("Swipe Right Detected")
                        if ws is not None:  # 检查WebSocket连接是否已建立
                            send_message(ws, "next_tab")
                    elif direction == "left":
                        print("Swipe Left Detected")
                        if ws is not None:  # 检查WebSocket连接是否已建立
                            send_message(ws, "previous_tab")
                    
                    slide_count = 0  # 重置计数器

    cv2.imshow('Hand Gesture Detection', frame)

    if cv2.waitKey(1) & 0xFF == 27:  # 按Esc键退出
        break

cap.release()
cv2.destroyAllWindows()
