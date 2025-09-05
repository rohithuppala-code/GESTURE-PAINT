# ☝️ Index only → Draw
# ✌️ Index + Middle → Hover
# ✋ All 5 fingers UP → Erase
# 🤏 Pinch (thumb + index) → Adjust brush size (applies to all colors)
# ✊ FIST (all fingers closed) → Next color
# keyboard c clears canvas
# keyboard q quits
# Touch colors → Select specific color
import cv2
import mediapipe as mp
import numpy as np
import time

# Mediapipe setup
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1, 
    min_detection_confidence=0.8,
    min_tracking_confidence=0.7
)

# Settings
colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 0, 0), (0, 255, 255), (0, 165, 255)]
color_names = ["Red", "Green", "Blue", "Black", "Yellow", "Orange"]
current_color_index = 0
brush_color = colors[current_color_index]
brush_thickness = 3  # Global brush thickness - stays same for all colors
min_thickness = 1
max_thickness = 50
eraser_size = 30

# State
drawing = False
prev_x, prev_y = 0, 0
last_color_change_time = 0  # For color change delay
color_changed_this_frame = False  # Flag to prevent showing text when color just changed

def get_fingers_up(lm_list):
    """Simple finger detection for right hand"""
    if len(lm_list) < 21:
        return [0, 0, 0, 0, 0]
    
    fingers = []
    
    # Thumb - for right hand, thumb up means tip is to the LEFT of joint
    if lm_list[4][0] < lm_list[3][0]:
        fingers.append(1)
    else:
        fingers.append(0)
    
    # Other fingers - same logic (tip higher than joint)
    for tip in [8, 12, 16, 20]:
        if lm_list[tip][1] < lm_list[tip-2][1]:
            fingers.append(1)
        else:
            fingers.append(0)
    
    return fingers

def distance(p1, p2):
    """Calculate distance between two points"""
    return int(((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5)

def select_color(x, y):
    """Check if touching color palette"""
    if 20 <= y <= 70:  # In color area
        for i in range(len(colors)):
            color_x = 20 + i * 60
            if color_x <= x <= color_x + 50:
                return i
    return None

def main():
    global brush_color, current_color_index, brush_thickness
    global drawing, prev_x, prev_y, last_color_change_time, color_changed_this_frame
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    canvas = None
    print("Enhanced Hand Drawing App Started!")
    print("Gestures: Index=Draw, Palm=Erase, Pinch=Size, Fist=Next Color")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        if canvas is None:
            canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
        
        # Reset color change flag
        color_changed_this_frame = False
        
        # Process frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        
        current_drawing = False
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Get hand points
                lm_list = []
                for lm in hand_landmarks.landmark:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append((cx, cy))
                
                fingers = get_fingers_up(lm_list)
                fingers_count = sum(fingers)
                
                if len(lm_list) >= 21:
                    x, y = lm_list[8]  # Index finger tip
                    thumb_x, thumb_y = lm_list[4]  # Thumb tip
                    
                    # 1. DRAW - Only index finger up
                    if fingers == [0, 1, 0, 0, 0]:
                        # Check color selection first
                        selected_color_index = select_color(x, y)
                        if selected_color_index is not None:
                            current_color_index = selected_color_index
                            brush_color = colors[current_color_index]
                            cv2.putText(frame, f"{color_names[current_color_index]}!", (x+20, y), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                        else:
                            # Draw - using global brush_thickness
                            if drawing:
                                cv2.line(canvas, (prev_x, prev_y), (x, y), brush_color, brush_thickness)
                            else:
                                drawing = True
                            
                            prev_x, prev_y = x, y
                            current_drawing = True
                        
                        cv2.circle(frame, (x, y), brush_thickness, brush_color, -1)
                    
                    # 2. HOVER - Index + Middle fingers up (no drawing)
                    elif fingers == [0, 1, 1, 0, 0]:
                        cv2.circle(frame, (x, y), brush_thickness, (255, 255, 255), 2)
                        cv2.putText(frame, "HOVER", (x+20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
                    
                    # 3. ERASE - All fingers up (palm open)
                    elif fingers_count == 5:
                        cv2.circle(canvas, (x, y), eraser_size, (255, 255, 255), -1)
                        cv2.circle(frame, (x, y), eraser_size, (0, 255, 255), 2)
                        cv2.putText(frame, "ERASE", (x+20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
                    
                    # 4. BRUSH SIZE - Pinch (thumb + index) - ONLY when pinching
                    elif fingers == [1, 1, 0, 0, 0] and fingers_count == 2:
                        pinch_distance = distance((thumb_x, thumb_y), (x, y))
                        # Update global brush thickness
                        brush_thickness = max(min_thickness, min(max_thickness, pinch_distance // 2))
                        
                        cv2.circle(frame, (x, y), brush_thickness, brush_color, 2)
                        cv2.putText(frame, f"SIZE: {brush_thickness}", (x+20, y), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)
                    
                    # 5. COLOR CYCLE - All fingers closed (fist)
                    elif fingers_count == 0:  # All fingers down (fist)
                        current_time = time.time()
                        if current_time - last_color_change_time > 1.0:  # 1 second delay
                            current_color_index = (current_color_index + 1) % len(colors)
                            brush_color = colors[current_color_index]
                            last_color_change_time = current_time
                            color_changed_this_frame = True
                            print(f"Color changed to: {color_names[current_color_index]}")
                        
                        # Only show text if color didn't just change and we're still in cooldown
                        if not color_changed_this_frame:
                            time_remaining = 1.0 - (current_time - last_color_change_time)
                            if time_remaining > 0:
                                cv2.putText(frame, f"CHANGING...", (x+20, y), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)  # White color
                            else:
                                cv2.putText(frame, f"FIST", (x+20, y), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)  # White color
                
                # Show hand landmarks
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        
        # Stop drawing when finger lifted
        if not current_drawing and drawing:
            drawing = False
        
        # Combine frame with canvas
        gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        
        frame_bg = cv2.bitwise_and(frame, frame, mask=mask)
        canvas_fg = cv2.bitwise_and(canvas, canvas, mask=mask_inv)
        result = cv2.add(frame_bg, canvas_fg)
        
        # UI - Extended Color palette
        for i, color in enumerate(colors):
            x = 20 + i * 60
            cv2.rectangle(result, (x, 20), (x+50, 70), color, -1)
            cv2.rectangle(result, (x, 20), (x+50, 70), (0, 0, 0), 1)
            
            # Highlight current color
            if i == current_color_index:
                cv2.rectangle(result, (x-3, 17), (x+53, 73), (255,255,255), 3)
        
        # Current color and brush info (moved to right side)
        info_text = f"{color_names[current_color_index]} | Size: {brush_thickness}"
        cv2.putText(result, info_text, (w-250, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, brush_color, 2)
        
        # Show color change notification
        if color_changed_this_frame:
            cv2.putText(result, f"Color: {color_names[current_color_index]}!", 
                       (w//2 - 100, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, brush_color, 3)
        
        # Updated instructions
        cv2.putText(result, "INDEX: Draw | PALM: Erase | PINCH: Size | FIST: Next Color", 
                   (10, h-30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        
        cv2.imshow("Enhanced Hand Drawing", result)
        
        # Keyboard controls
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
            print("Canvas cleared")
    
    cap.release()
    cv2.destroyAllWindows()
    print("Application closed")

if __name__ == "__main__":
    main()