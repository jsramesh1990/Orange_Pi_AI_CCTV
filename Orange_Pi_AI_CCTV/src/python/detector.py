# src/python/detector.py
import ctypes
import numpy as np
import cv2
from typing import List, Dict, Any
import threading
import queue
import time
import psycopg2
import redis
import json
import os

# Load C libraries
rtsp_lib = ctypes.CDLL('./lib/librtsp_capture.so')
motion_lib = ctypes.CDLL('./lib/libmotion_detection.so')
tracker_lib = ctypes.CDLL('./lib/libdeepsort.so')

class Detection:
    def __init__(self, x1, y1, x2, y2, conf, class_id, class_name, track_id=-1):
        self.bbox = [x1, y1, x2, y2]
        self.confidence = conf
        self.class_id = class_id
        self.class_name = class_name
        self.track_id = track_id

class YOLODetector:
    def __init__(self, model_path: str, use_npu: bool = False):
        self.model_path = model_path
        self.use_npu = use_npu
        
        # Load YOLO model (using ONNX Runtime or custom C++ inference)
        if use_npu:
            from cpp_bridge import NPUInference
            self.session = NPUInference(model_path)
        else:
            import onnxruntime as ort
            self.session = ort.InferenceSession(model_path)
        
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        
        self.input_shape = self.session.get_inputs()[0].shape
        self.confidence_threshold = 0.5
        self.iou_threshold = 0.45
        
        self.classes = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
                        'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
                        'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
                        'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
                        'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
                        'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
                        'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
                        'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
                        'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
                        'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
                        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
                        'toothbrush']
    
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        # Resize and normalize
        img = cv2.resize(frame, (self.input_shape[2], self.input_shape[3]))
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)
        return img
    
    def postprocess(self, outputs: np.ndarray, frame_shape: tuple) -> List[Detection]:
        detections = []
        original_h, original_w = frame_shape[:2]
        
        # Parse YOLO output (simplified - actual format depends on model)
        for detection in outputs[0]:
            if detection[4] > self.confidence_threshold:
                x1 = int((detection[0] - detection[2]/2) * original_w)
                y1 = int((detection[1] - detection[3]/2) * original_h)
                x2 = int((detection[0] + detection[2]/2) * original_w)
                y2 = int((detection[1] + detection[3]/2) * original_h)
                
                class_id = int(detection[5])
                confidence = detection[4]
                class_name = self.classes[class_id] if class_id < len(self.classes) else "unknown"
                
                detections.append(Detection(x1, y1, x2, y2, confidence, class_id, class_name))
        
        # NMS (Non-Maximum Suppression)
        detections = self.nms(detections)
        return detections
    
    def nms(self, detections: List[Detection]) -> List[Detection]:
        if not detections:
            return detections
        
        detections.sort(key=lambda x: x.confidence, reverse=True)
        keep = []
        
        while detections:
            best = detections.pop(0)
            keep.append(best)
            
            detections = [d for d in detections if self.iou(best.bbox, d.bbox) < self.iou_threshold]
        
        return keep
    
    def iou(self, bbox1: List[int], bbox2: List[int]) -> float:
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        return intersection / union
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        input_tensor = self.preprocess(frame)
        outputs = self.session.run([self.output_name], {self.input_name: input_tensor})
        detections = self.postprocess(outputs[0], frame.shape)
        return detections

class DatabaseManager:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, database=database
        )
        self.cursor = self.conn.cursor()
        self.init_tables()
    
    def init_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id SERIAL PRIMARY KEY,
                camera_id INTEGER,
                track_id INTEGER,
                object_type VARCHAR(50),
                confidence FLOAT,
                bbox_x1 FLOAT, bbox_y1 FLOAT, bbox_x2 FLOAT, bbox_y2 FLOAT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_path TEXT,
                video_path TEXT
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_events (
                id SERIAL PRIMARY KEY,
                person_name VARCHAR(100),
                confidence FLOAT,
                camera_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_path TEXT
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS license_plates (
                id SERIAL PRIMARY KEY,
                plate_number VARCHAR(20),
                confidence FLOAT,
                camera_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_path TEXT
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                alert_type VARCHAR(50),
                severity INTEGER,
                message TEXT,
                camera_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged BOOLEAN DEFAULT FALSE
            )
        """)
        
        self.conn.commit()
    
    def save_detection(self, camera_id: int, detection: Detection, image_path: str = None):
        self.cursor.execute("""
            INSERT INTO detections 
            (camera_id, track_id, object_type, confidence, 
             bbox_x1, bbox_y1, bbox_x2, bbox_y2, image_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (camera_id, detection.track_id, detection.class_name, detection.confidence,
              detection.bbox[0], detection.bbox[1], detection.bbox[2], detection.bbox[3], image_path))
        self.conn.commit()
    
    def save_alert(self, alert_type: str, severity: int, message: str, camera_id: int):
        self.cursor.execute("""
            INSERT INTO alerts (alert_type, severity, message, camera_id)
            VALUES (%s, %s, %s, %s)
        """, (alert_type, severity, message, camera_id))
        self.conn.commit()
    
    def get_recent_detections(self, object_type: str, minutes: int = 5) -> List[Dict]:
        self.cursor.execute("""
            SELECT * FROM detections 
            WHERE object_type = %s 
            AND timestamp > NOW() - INTERVAL '%s minutes'
            ORDER BY timestamp DESC
        """, (object_type, minutes))
        return self.cursor.fetchall()

class RedisManager:
    def __init__(self, host: str, port: int, password: str = None):
        self.client = redis.Redis(host=host, port=port, password=password, decode_responses=True)
    
    def publish_alert(self, alert_type: str, message: str, image_path: str = None):
        data = {
            'type': alert_type,
            'message': message,
            'image_path': image_path,
            'timestamp': time.time()
        }
        self.client.publish('alerts', json.dumps(data))
    
    def cache_frame(self, frame_id: str, frame_data: bytes, ttl: int = 60):
        self.client.setex(f'frame:{frame_id}', ttl, frame_data)
    
    def get_frame(self, frame_id: str) -> bytes:
        return self.client.get(f'frame:{frame_id}')

class CCTVSystem:
    def __init__(self, config_path: str = "/etc/cctv/config.json"):
        self.load_config(config_path)
        
        self.detector = YOLODetector(self.model_path, self.use_npu)
        self.db = DatabaseManager(self.db_host, self.db_port, self.db_user, 
                                  self.db_password, self.db_name)
        self.redis_client = RedisManager(self.redis_host, self.redis_port, self.redis_password)
        
        self.camera_threads = []
        self.frame_queues = {}
        self.running = False
        
        # Initialize C libraries
        self.init_c_libraries()
    
    def load_config(self, config_path: str):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.cameras = config.get('cameras', [])
        self.db_host = config.get('database', {}).get('host', 'localhost')
        self.db_port = config.get('database', {}).get('port', 5432)
        self.db_user = config.get('database', {}).get('user', 'cctv')
        self.db_password = config.get('database', {}).get('password', '')
        self.db_name = config.get('database', {}).get('name', 'cctv')
        
        self.redis_host = config.get('redis', {}).get('host', 'localhost')
        self.redis_port = config.get('redis', {}).get('port', 6379)
        self.redis_password = config.get('redis', {}).get('password', None)
        
        self.model_path = config.get('model', {}).get('yolo_path', './models/yolov8n.onnx')
        self.use_npu = config.get('hardware', {}).get('use_npu', False)
    
    def init_c_libraries(self):
        """Initialize C library bindings"""
        # RTSP capture functions
        self.rtsp_init = rtsp_lib.rtsp_init
        self.rtsp_init.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.rtsp_init.restype = ctypes.c_void_p
        
        self.rtsp_start = rtsp_lib.rtsp_start
        self.rtsp_start.argtypes = [ctypes.c_void_p]
        self.rtsp_start.restype = ctypes.c_int
        
        self.rtsp_get_frame = rtsp_lib.rtsp_get_frame
        self.rtsp_get_frame.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.rtsp_get_frame.restype = ctypes.c_void_p
        
        # Motion detection
        self.motion_init = motion_lib.motion_init
        self.motion_detect = motion_lib.motion_detect
        
        # Tracker
        self.tracker_init = tracker_lib.DeepSORT_new
        self.tracker_update = tracker_lib.DeepSORT_update
    
    def camera_worker(self, camera_id: int, rtsp_url: str, username: str, password: str):
        """Worker thread for each camera"""
        frame_queue = self.frame_queues[camera_id]
        
        # Initialize RTSP capture using C library
        camera_config = (ctypes.c_char * 1024)()
        # ... set camera config
        
        session = self.rtsp_init(camera_config, 30)
        self.rtsp_start(session)
        
        while self.running:
            # Get frame from C library
            frame_ptr = self.rtsp_get_frame(session, 33)  # 33ms timeout
            if frame_ptr:
                # Convert to numpy array
                frame = self.convert_frame_to_numpy(frame_ptr)
                
                # Process frame
                detections = self.detector.detect(frame)
                
                # Update tracker
                track_ids = self.update_tracker(camera_id, detections)
                
                # Store results
                for det in detections:
                    self.db.save_detection(camera_id, det)
                    
                    # Check for alerts
                    self.check_alerts(camera_id, det, frame)
                
                # Publish to Redis for other services
                self.redis_client.publish_alert('detection', 
                    f"Detected {len(detections)} objects", None)
                
                # Add to queue for dashboard
                frame_queue.put((frame, detections))
                
                # Release frame
                self.release_frame(frame_ptr)
        
        self.rtsp_stop(session)
    
    def update_tracker(self, camera_id: int, detections: List[Detection]) -> List[int]:
        """Update DeepSORT tracker (C++ library)"""
        # Prepare detections for C++ tracker
        det_array = (ctypes.c_float * (len(detections) * 6))()
        for i, det in enumerate(detections):
            det_array[i*6] = det.bbox[0]
            det_array[i*6+1] = det.bbox[1]
            det_array[i*6+2] = det.bbox[2]
            det_array[i*6+3] = det.bbox[3]
            det_array[i*6+4] = det.confidence
            det_array[i*6+5] = det.class_id
        
        # Call C++ tracker
        track_ids_ptr = self.tracker_update(self.trackers[camera_id], det_array, len(detections))
        
        # Parse results
        track_ids = []
        for i in range(len(detections)):
            detections[i].track_id = track_ids_ptr[i]
            track_ids.append(track_ids_ptr[i])
        
        return track_ids
    
    def check_alerts(self, camera_id: int, detection: Detection, frame: np.ndarray):
        """Check if detection triggers any alerts"""
        # Person detection after hours
        if detection.class_name == 'person':
            current_hour = time.localtime().tm_hour
            if current_hour < 6 or current_hour > 22:
                self.db.save_alert('person_detected', 5, 
                    f"Person detected on camera {camera_id} after hours", camera_id)
                self.redis_client.publish_alert('security', 
                    f"⚠️ Person detected after hours on camera {camera_id}")
                
                # Save snapshot
                snapshot_path = self.save_snapshot(frame, detection)
                self.redis_client.publish_alert('security', 
                    f"Person detected after hours", snapshot_path)
        
        # Package detection (doorbell)
        elif detection.class_name == 'package' or detection.class_name == 'suitcase':
            self.db.save_alert('package_delivered', 3, 
                f"Package detected on camera {camera_id}", camera_id)
            self.redis_client.publish_alert('package', 
                f"📦 Package delivery detected on camera {camera_id}")
        
        # Vehicle in restricted zone
        elif detection.class_name in ['car', 'motorcycle', 'truck']:
            # Check if vehicle entered restricted zone
            if self.is_in_restricted_zone(detection.bbox):
                self.db.save_alert('vehicle_restricted', 4, 
                    f"Vehicle entered restricted zone on camera {camera_id}", camera_id)
                self.redis_client.publish_alert('security', 
                    f"🚗 Vehicle in restricted zone on camera {camera_id}")
    
    def is_in_restricted_zone(self, bbox: List[int]) -> bool:
        # Define restricted zones (simplified)
        restricted_zones = [
            {'x1': 100, 'y1': 100, 'x2': 300, 'y2': 300},  # Example zone
        ]
        
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        
        for zone in restricted_zones:
            if (zone['x1'] < center_x < zone['x2'] and 
                zone['y1'] < center_y < zone['y2']):
                return True
        return False
    
    def save_snapshot(self, frame: np.ndarray, detection: Detection) -> str:
        """Save snapshot image with bounding box"""
        import os
        from datetime import datetime
        
        # Draw bounding box
        img = frame.copy()
        cv2.rectangle(img, 
                     (int(detection.bbox[0]), int(detection.bbox[1])),
                     (int(detection.bbox[2]), int(detection.bbox[3])),
                     (0, 255, 0), 2)
        
        label = f"{detection.class_name} ({detection.confidence:.2f})"
        if detection.track_id >= 0:
            label += f" ID:{detection.track_id}"
        
        cv2.putText(img, label, 
                   (int(detection.bbox[0]), int(detection.bbox[1]) - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Save to disk
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"/var/cctv/snapshots/{timestamp}_{detection.class_name}.jpg"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        cv2.imwrite(filename, img)
        
        return filename
    
    def convert_frame_to_numpy(self, frame_ptr) -> np.ndarray:
        """Convert C frame structure to numpy array"""
        # Assuming frame_ptr points to a Frame struct with data pointer
        # This is simplified - actual implementation would use ctypes structure
        width = ctypes.cast(frame_ptr + 8, ctypes.POINTER(ctypes.c_int)).contents.value
        height = ctypes.cast(frame_ptr + 12, ctypes.POINTER(ctypes.c_int)).contents.value
        
        data_ptr = ctypes.cast(frame_ptr, ctypes.POINTER(ctypes.c_uint8))
        size = width * height * 3
        arr = np.ctypeslib.as_array(data_ptr, shape=(size,))
        
        return arr.reshape((height, width, 3))
    
    def release_frame(self, frame_ptr):
        """Release frame back to C library"""
        # Call C free function
        ctypes.CDLL(None).free(frame_ptr)
    
    def start(self):
        self.running = True
        
        for i, camera in enumerate(self.cameras):
            self.frame_queues[i] = queue.Queue(maxsize=10)
            thread = threading.Thread(
                target=self.camera_worker,
                args=(i, camera['rtsp_url'], camera.get('username', ''), 
                      camera.get('password', '')),
                daemon=True
            )
            thread.start()
            self.camera_threads.append(thread)
        
        # Start alert processor
        self.alert_thread = threading.Thread(target=self.process_alerts, daemon=True)
        self.alert_thread.start()
    
    def process_alerts(self):
        """Process alerts from Redis and send to Telegram"""
        from src.python.telegram_bot import TelegramBot
        
        bot = TelegramBot(os.getenv('TELEGRAM_TOKEN'), os.getenv('TELEGRAM_CHAT_ID'))
        
        pubsub = self.redis_client.client.pubsub()
        pubsub.subscribe('alerts')
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                alert = json.loads(message['data'])
                bot.send_alert(alert['message'], alert.get('image_path'))
    
    def stop(self):
        self.running = False
        for thread in self.camera_threads:
            thread.join(timeout=5)

if __name__ == '__main__':
    system = CCTVSystem('/etc/cctv/config.json')
    system.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        system.stop()
