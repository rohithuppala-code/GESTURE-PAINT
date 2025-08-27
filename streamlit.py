import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import time
from PIL import Image
import io
import base64

# Configure page
st.set_page_config(
    page_title="✋ AI Hand Drawing Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .gesture-guide {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        text-align: center;
        font-weight: bold;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-active { background-color: #28a745; }
    .status-inactive { background-color: #dc3545; }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'canvas' not in st.session_state:
    st.session_state.canvas = None
if 'drawing' not in st.session_state:
    st.session_state.drawing = False
if 'current_color_index' not in st.session_state:
    st.session_state.current_color_index = 0
if 'brush_thickness' not in st.session_state:
    st.session_state.brush_thickness = 5
if 'camera_active' not in st.session_state:
    st.session_state.camera_active = False

# Initialize MediaPipe
@st.cache_resource
def initialize_mediapipe():
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.8,
        min_tracking_confidence=0.7
    )
    return mp_hands, mp_draw, hands

mp_hands, mp_draw, hands = initialize_mediapipe()

# Drawing settings
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 0, 0), (255, 255, 0), (255, 165, 0)]
color_names = ["Red", "Green", "Blue", "Black", "Yellow", "Orange"]
color_hex = ["#FF0000", "#00FF00", "#0000FF", "#000000", "#FFFF00", "#FFA500"]

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

def process_frame(frame, canvas):
    """Process frame with hand detection and drawing"""
    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]
    
    if canvas is None:
        canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
    
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    
    gesture_info = {"gesture": "No Hand Detected", "confidence": 0.0}
    
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
                
                # Gesture recognition and drawing logic
                if fingers == [0, 1, 0, 0, 0]:
                    # Drawing mode
                    brush_color = colors[st.session_state.current_color_index]
                    if st.session_state.drawing:
                        cv2.line(canvas, (st.session_state.prev_x, st.session_state.prev_y), 
                               (x, y), brush_color, st.session_state.brush_thickness)
                    
                    st.session_state.prev_x, st.session_state.prev_y = x, y
                    st.session_state.drawing = True
                    cv2.circle(frame, (x, y), st.session_state.brush_thickness, brush_color, -1)
                    gesture_info = {"gesture": "✏️ Drawing", "confidence": 1.0}
                
                elif fingers == [0, 1, 1, 0, 0]:
                    # Hover mode
                    cv2.circle(frame, (x, y), st.session_state.brush_thickness, (255, 255, 255), 2)
                    gesture_info = {"gesture": "👆 Hovering", "confidence": 1.0}
                    st.session_state.drawing = False
                
                elif fingers_count == 5:
                    # Erase mode
                    cv2.circle(canvas, (x, y), 30, (255, 255, 255), -1)
                    cv2.circle(frame, (x, y), 30, (0, 255, 255), 2)
                    gesture_info = {"gesture": "🧽 Erasing", "confidence": 1.0}
                    st.session_state.drawing = False
                
                elif fingers == [1, 1, 0, 0, 0] and fingers_count == 2:
                    # Brush size adjustment
                    pinch_distance = distance((thumb_x, thumb_y), (x, y))
                    st.session_state.brush_thickness = max(1, min(50, pinch_distance // 2))
                    cv2.circle(frame, (x, y), st.session_state.brush_thickness, colors[st.session_state.current_color_index], 2)
                    gesture_info = {"gesture": f"📏 Sizing ({st.session_state.brush_thickness}px)", "confidence": 1.0}
                    st.session_state.drawing = False
                
                elif fingers_count == 0:
                    # Color change mode
                    gesture_info = {"gesture": "🎨 Ready to Change Color", "confidence": 1.0}
                    st.session_state.drawing = False
            
            # Draw hand landmarks
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    else:
        st.session_state.drawing = False
    
    # Combine frame with canvas
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)
    
    frame_bg = cv2.bitwise_and(frame, frame, mask=mask)
    canvas_fg = cv2.bitwise_and(canvas, canvas, mask=mask_inv)
    result = cv2.add(frame_bg, canvas_fg)
    
    return result, canvas, gesture_info

# Header
st.markdown("""
<div class="main-header">
    <h1>🎨 AI Hand Drawing Studio</h1>
    <p>Create amazing artwork using just your hand gestures!</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")
    
    # Camera controls
    st.markdown("#### 📹 Camera")
    camera_col1, camera_col2 = st.columns(2)
    
    with camera_col1:
        if st.button("▶️ Start Camera", type="primary"):
            st.session_state.camera_active = True
            st.rerun()
    
    with camera_col2:
        if st.button("⏹️ Stop Camera"):
            st.session_state.camera_active = False
            st.rerun()
    
    # Color palette
    st.markdown("#### 🎨 Color Palette")
    selected_color = st.selectbox(
        "Choose Color:",
        options=list(range(len(color_names))),
        format_func=lambda x: f"{color_names[x]}",
        index=st.session_state.current_color_index
    )
    
    if selected_color != st.session_state.current_color_index:
        st.session_state.current_color_index = selected_color
    
    # Color preview
    st.markdown(f"""
    <div style="background-color: {color_hex[st.session_state.current_color_index]}; 
                height: 50px; border-radius: 5px; border: 2px solid #333;
                display: flex; align-items: center; justify-content: center;
                color: {'white' if st.session_state.current_color_index == 3 else 'black'};
                font-weight: bold;">
        Current Color: {color_names[st.session_state.current_color_index]}
    </div>
    """, unsafe_allow_html=True)
    
    # Brush settings
    st.markdown("#### 🖌️ Brush Settings")
    brush_size = st.slider("Brush Size", 1, 50, st.session_state.brush_thickness)
    st.session_state.brush_thickness = brush_size
    
    # Clear canvas
    st.markdown("#### 🗑️ Actions")
    if st.button("Clear Canvas", type="secondary"):
        st.session_state.canvas = None
        st.success("Canvas cleared!")
    
    # Download canvas
    if st.session_state.canvas is not None:
        canvas_pil = Image.fromarray(cv2.cvtColor(st.session_state.canvas, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        canvas_pil.save(buf, format="PNG")
        st.download_button(
            label="💾 Download Artwork",
            data=buf.getvalue(),
            file_name="hand_drawing.png",
            mime="image/png"
        )

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📺 Live Camera Feed")
    
    if st.session_state.camera_active:
        # Placeholder for camera feed
        video_placeholder = st.empty()
        
        # Initialize camera
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            while st.session_state.camera_active:
                ret, frame = cap.read()
                if not ret:
                    st.error("Failed to access camera")
                    break
                
                # Process frame
                processed_frame, st.session_state.canvas, gesture_info = process_frame(frame, st.session_state.canvas)
                
                # Convert to RGB for display
                rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                video_placeholder.image(rgb_frame, channels="RGB", use_column_width=True)
                
                # Update gesture info in sidebar
                with col2:
                    st.markdown("### 👋 Gesture Status")
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>{gesture_info['gesture']}</h4>
                        <p>Confidence: {gesture_info['confidence']:.1%}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                time.sleep(0.1)  # Control frame rate
        else:
            st.error("Cannot access camera. Please check your camera permissions.")
        
        cap.release()
    else:
        st.info("👆 Click 'Start Camera' to begin drawing with hand gestures!")
        
        # Show demo image or instructions
        st.markdown("""
        <div class="feature-card">
            <h4>🚀 Get Started:</h4>
            <ol>
                <li>Click "Start Camera" in the sidebar</li>
                <li>Allow camera permissions when prompted</li>
                <li>Use hand gestures to draw and control the application</li>
                <li>Download your artwork when finished!</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("### 🎯 Gesture Guide")
    
    gestures = [
        ("✏️ Draw", "Index finger only", "#28a745"),
        ("👆 Hover", "Index + Middle fingers", "#17a2b8"),
        ("🧽 Erase", "Open palm (all fingers)", "#ffc107"),
        ("📏 Resize", "Pinch (thumb + index)", "#fd7e14"),
        ("🎨 Color", "Closed fist", "#6f42c1")
    ]
    
    for gesture, description, color in gestures:
        st.markdown(f"""
        <div style="background: {color}; color: white; padding: 0.8rem; 
                    border-radius: 5px; margin: 0.5rem 0; text-align: center;">
            <strong>{gesture}</strong><br>
            <small>{description}</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Performance metrics
    st.markdown("### 📊 Session Stats")
    
    metrics_col1, metrics_col2 = st.columns(2)
    with metrics_col1:
        st.metric("Current Color", color_names[st.session_state.current_color_index])
    with metrics_col2:
        st.metric("Brush Size", f"{st.session_state.brush_thickness}px")
    
    # Camera status
    camera_status = "🟢 Active" if st.session_state.camera_active else "🔴 Inactive"
    st.markdown(f"""
    <div class="metric-card">
        <h4>Camera Status</h4>
        <p>{camera_status}</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🎨 <strong>AI Hand Drawing Studio</strong> - Create art with the power of computer vision!</p>
    <p><small>Built with Streamlit, OpenCV, and MediaPipe</small></p>
</div>
""", unsafe_allow_html=True)