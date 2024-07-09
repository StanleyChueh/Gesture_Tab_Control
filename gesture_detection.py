import cv2
import mediapipe as mp

# 初始化MediaPipe Hands模型
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

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
            if max(x_coords) - min(x_coords) > 0.5:  # 手势横向跨度大于0.5认为是滑动
                if x_coords[0] < x_coords[-1]:  # 从左向右滑动
                    print("Swipe Right Detected")
                    # 这里可以添加切换到下一页的逻辑
                else:  # 从右向左滑动
                    print("Swipe Left Detected")
                    # 这里可以添加切换到上一页的逻辑

    cv2.imshow('Hand Gesture Detection', frame)

    if cv2.waitKey(1) & 0xFF == 27:  # 按Esc键退出
        break

cap.release()
cv2.destroyAllWindows()
