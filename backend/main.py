from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import cv2
import mediapipe as mp
import numpy as np
import time
import base64
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, cors_allowed_origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Global variables
camera = None
canvas = None
camera_active = False
streaming_active = False
drawing_state = {
    'gesture': 'Ready',
    'color': 'Red',
    'color_index': 0,
    'brush_size': 5,
    'drawing': False,
    'prev_x': 0,
    'prev_y': 0,
    'last_thumb_time': 0
}

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
min_thickness = 1
max_thickness = 50
eraser_size = 30
CAMERA_WIDTH = 640  # Reduced resolution
CAMERA_HEIGHT = 480
JPEG_QUALITY = 70  # Lower quality for smaller data size

def get_fingers_up(lm_list):
    """Simple finger detection for right hand"""
    if len(lm_list) < 21:
        return [0, 0, 0, 0, 0]
    
    fingers = []
    if lm_list[4][0] < lm_list[3][0]:
        fingers.append(1)
    else:
        fingers.append(0)
    
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
    if 20 <= y <= 70:
        for i in range(len(colors)):
            color_x = 20 + i * 60
            if color_x <= x <= color_x + 50:
                return i
    return None

def process_frame():
    """Process camera frame and detect hand gestures"""
    global canvas, drawing_state
    
    start_time = time.time()
    
    if not camera_active or camera is None:
        logger.warning("Camera not active or not initialized")
        return None, None
    
    ret, frame = camera.read()
    if not ret:
        logger.error("Failed to read frame from camera")
        return None, None
    
    # Resize frame
    frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]
    
    if canvas is None:
        canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
    
    # Process frame only if hands are detected
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    
    current_drawing = False
    current_gesture = 'Ready'
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            lm_list = []
            for lm in hand_landmarks.landmark:
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append((cx, cy))
            
            fingers = get_fingers_up(lm_list)
            fingers_count = sum(fingers)
            
            if len(lm_list) >= 21:
                x, y = lm_list[8]
                thumb_x, thumb_y = lm_list[4]
                
                if fingers == [0, 1, 0, 0, 0]:
                    current_gesture = 'Drawing'
                    selected_color_index = select_color(x, y)
                    if selected_color_index is not None:
                        drawing_state['color_index'] = selected_color_index
                        drawing_state['color'] = color_names[selected_color_index]
                        current_gesture = f'Color: {color_names[selected_color_index]}'
                    else:
                        brush_color = colors[drawing_state['color_index']]
                        if drawing_state['drawing']:
                            cv2.line(canvas, (drawing_state['prev_x'], drawing_state['prev_y']), 
                                   (x, y), brush_color, drawing_state['brush_size'])
                        else:
                            drawing_state['drawing'] = True
                        
                        drawing_state['prev_x'], drawing_state['prev_y'] = x, y
                        current_drawing = True
                    
                    cv2.circle(frame, (x, y), drawing_state['brush_size'], 
                             colors[drawing_state['color_index']], -1)
                
                elif fingers == [0, 1, 1, 0, 0]:
                    current_gesture = 'Hover'
                    cv2.circle(frame, (x, y), drawing_state['brush_size'], (255, 255, 255), 2)
                    cv2.putText(frame, "HOVER", (x+20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
                
                elif fingers_count == 5:
                    current_gesture = 'Erasing'
                    cv2.circle(canvas, (x, y), eraser_size, (255, 255, 255), -1)
                    cv2.circle(frame, (x, y), eraser_size, (0, 255, 255), 2)
                    cv2.putText(frame, "ERASE", (x+20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
                
                elif fingers == [1, 1, 0, 0, 0] and fingers_count == 2:
                    current_gesture = 'Adjusting Size'
                    pinch_distance = distance((thumb_x, thumb_y), (x, y))
                    new_thickness = max(min_thickness, min(max_thickness, pinch_distance // 2))
                    drawing_state['brush_size'] = new_thickness
                    cv2.circle(frame, (x, y), drawing_state['brush_size'], 
                             colors[drawing_state['color_index']], 2)
                    cv2.putText(frame, f"SIZE: {drawing_state['brush_size']}", (x+20, y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)
                
                elif fingers_count == 0:
                    current_time = time.time()
                    if current_time - drawing_state['last_thumb_time'] > 1.0:
                        drawing_state['color_index'] = (drawing_state['color_index'] + 1) % len(colors)
                        drawing_state['color'] = color_names[drawing_state['color_index']]
                        drawing_state['last_thumb_time'] = current_time
                        current_gesture = f'Next Color: {drawing_state["color"]}'
                    next_color_idx = (drawing_state['color_index'] + 1) % len(colors)
                    cv2.putText(frame, f"NEXT: {color_names[next_color_idx]}", 
                               (x+20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
            
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    
    if not current_drawing and drawing_state['drawing']:
        drawing_state['drawing'] = False
    
    drawing_state['gesture'] = current_gesture
    
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)
    
    frame_bg = cv2.bitwise_and(frame, frame, mask=mask)
    canvas_fg = cv2.bitwise_and(canvas, canvas, mask=mask_inv)
    result = cv2.add(frame_bg, canvas_fg)
    
    for i, color in enumerate(colors):
        x = 20 + i * 60
        cv2.rectangle(result, (x, 20), (x+50, 70), color, -1)
        cv2.rectangle(result, (x, 20), (x+50, 70), (0, 0, 0), 1)
        if i == drawing_state['color_index']:
            cv2.rectangle(result, (x-3, 17), (x+53, 73), (255,255,255), 3)
    
    info_text = f"{drawing_state['color']} | Size: {drawing_state['brush_size']}"
    cv2.putText(result, info_text, (w-250, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, colors[drawing_state['color_index']], 2)
    
    processing_time = (time.time() - start_time) * 1000
    logger.debug(f"Frame processing time: {processing_time:.2f}ms")
    
    return result, canvas

def stream_frames():
    """Stream frames via WebSocket"""
    global streaming_active
    
    while streaming_active and camera_active:
        try:
            start_time = time.time()
            result_frame, current_canvas = process_frame()
            
            if result_frame is not None:
                _, buffer = cv2.imencode('.jpg', result_frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                logger.debug(f"Emitting frame_update: gesture={drawing_state['gesture']}, color={drawing_state['color']}, frame_size={len(frame_base64)}")
                socketio.emit('frame_update', {
                    'frame': f'data:image/jpeg;base64,{frame_base64}',
                    'state': {
                        'gesture': drawing_state['gesture'],
                        'color': drawing_state['color'],
                        'brush_size': drawing_state['brush_size'],
                        'drawing': drawing_state['drawing']
                    }
                })
            
            elapsed = (time.time() - start_time) * 1000
            sleep_time = max(0, (33 - elapsed) / 1000)  # Target ~30 FPS
            time.sleep(sleep_time)
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            streaming_active = False
            socketio.emit('stream_status', {'active': False})
            break

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected to WebSocket')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected from WebSocket')

@socketio.on('start_stream')
def handle_start_stream():
    global streaming_active
    if camera_active and not streaming_active:
        streaming_active = True
        logger.info('Starting WebSocket stream')
        thread = threading.Thread(target=stream_frames)
        thread.daemon = True
        thread.start()
        emit('stream_status', {'active': True})

@socketio.on('stop_stream')
def handle_stop_stream():
    global streaming_active
    streaming_active = False
    logger.info('Stopping WebSocket stream')
    emit('stream_status', {'active': False})

@app.route('/api/start_camera', methods=['POST'])
def start_camera():
    """Initialize and start the camera"""
    global camera, camera_active, canvas
    
    try:
        if camera is None:
            logger.debug('Attempting to initialize camera with index 0')
            camera = cv2.VideoCapture(0)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        
        if not camera.isOpened():
            logger.error('Camera initialization failed')
            return jsonify({
                'error': 'Cannot open camera',
                'details': 'Check if camera is connected or try a different index (e.g., 1, 2)'
            }), 500
        
        ret, frame = camera.read()
        if not ret:
            camera.release()
            camera = None
            logger.error('Failed to read frame from camera')
            return jsonify({
                'error': 'Failed to read from camera',
                'details': 'Ensure camera is functional and not in use by another application'
            }), 500
        
        camera_active = True
        canvas = None
        logger.info('Camera started successfully')
        
        return jsonify({
            'status': 'Camera started successfully',
            'active': True
        })
    
    except Exception as e:
        logger.error(f'Camera start error: {str(e)}')
        return jsonify({
            'error': 'Failed to start camera',
            'details': str(e)
        }), 500

@app.route('/api/stop_camera', methods=['POST'])
def stop_camera():
    """Stop the camera"""
    global camera, camera_active, streaming_active
    
    try:
        camera_active = False
        streaming_active = False
        if camera is not None:
            camera.release()
            camera = None
            logger.info('Camera stopped and released')
        
        return jsonify({
            'status': 'Camera stopped successfully',
            'active': False
        })
    
    except Exception as e:
        logger.error(f'Camera stop error: {str(e)}')
        return jsonify({
            'error': 'Failed to stop camera',
            'details': str(e)
        }), 500

@app.route('/api/get_state', methods=['GET'])
def get_state():
    """Get current drawing state"""
    logger.debug('Fetching drawing state')
    return jsonify({
        'camera_active': camera_active,
        'gesture': drawing_state['gesture'],
        'color': drawing_state['color'],
        'color_index': drawing_state['color_index'],
        'brush_size': drawing_state['brush_size'],
        'drawing': drawing_state['drawing']
    })

@app.route('/api/set_color', methods=['POST'])
def set_color():
    """Manually set color"""
    data = request.get_json()
    color_name = data.get('color')
    
    if color_name in color_names:
        color_index = color_names.index(color_name)
        drawing_state['color_index'] = color_index
        drawing_state['color'] = color_name
        logger.info(f'Color set to {color_name}')
        
        return jsonify({
            'status': 'Color updated',
            'color': color_name,
            'color_index': color_index
        })
    
    logger.warning(f'Invalid color requested: {color_name}')
    return jsonify({'error': 'Invalid color'}), 400

@app.route('/api/clear_canvas', methods=['POST'])
def clear_canvas():
    """Clear the drawing canvas"""
    global canvas
    
    if camera_active and camera is not None:
        ret, frame = camera.read()
        if ret:
            frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
            logger.info('Canvas cleared')
    
    return jsonify({'status': 'Canvas cleared'})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.debug('Health check requested')
    return jsonify({
        'status': 'OK',
        'timestamp': time.time(),
        'camera_active': camera_active
    })

if __name__ == '__main__':
    logger.info("Starting Hand Gesture Drawing Flask Server with WebSocket...")
    logger.info("Available endpoints:")
    logger.info("- POST /api/start_camera - Start camera")
    logger.info("- POST /api/stop_camera - Stop camera") 
    logger.info("- GET /api/get_state - Get drawing state")
    logger.info("- POST /api/set_color - Set drawing color")
    logger.info("- POST /api/clear_canvas - Clear canvas")
    logger.info("- GET /api/health - Health check")
    logger.info("- WebSocket events: connect, disconnect, start_stream, stop_stream")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)