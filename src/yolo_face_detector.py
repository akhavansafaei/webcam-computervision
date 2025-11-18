# File: src/yolo_face_detector.py
"""
YOLO-based face detector for GPU acceleration
Uses local yolov8n.pt model with person detection
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from src.config import MIN_FACE_SIZE


class YOLOFaceDetector:
    """GPU-accelerated face detection using YOLOv8"""
    
    def __init__(self, auto_download: bool = False):
        """
        Initialize YOLO face detector
        
        Args:
            auto_download: Try to download model if not found (deprecated for local use)
        """
        self.model = None
        self.device = 'cpu'
        self.available = False
        self.use_person_detection = False
        
        # Check if ultralytics is available
        try:
            from ultralytics import YOLO
        except ImportError:
            print("❌ Ultralytics not installed")
            print("   Install with: pip install ultralytics")
            return
        
        # Look for model in multiple locations
        possible_paths = [
            # 1. Same directory as this file (src/)
            Path(__file__).parent / "yolov8n.pt",
            Path(__file__).parent / "yolov8n-face.pt",
            
            # 2. Models directory
            Path(__file__).parent.parent / "models" / "yolov8n.pt",
            Path(__file__).parent.parent / "models" / "yolov8n-face.pt",
            
            # 3. Project root
            Path(__file__).parent.parent / "yolov8n.pt",
            Path(__file__).parent.parent / "yolov8n-face.pt",
        ]
        
        model_path = None
        for path in possible_paths:
            if path.exists():
                model_path = path
                print(f"✅ Found YOLO model: {path}")
                
                # Check if it's face-specific or standard
                if "face" in path.name:
                    self.use_person_detection = False
                    print("   Model type: Face detection")
                else:
                    self.use_person_detection = True
                    print("   Model type: Person detection (will extract face region)")
                break
        
        if not model_path:
            print("❌ YOLO model not found in:")
            for path in possible_paths:
                print(f"   - {path}")
            print("   Place yolov8n.pt in src/ directory")
            return
        
        # Try to load model
        try:
            print(f"📂 Loading YOLO model from: {model_path}")
            self.model = YOLO(str(model_path))
            
            # Check if GPU is available
            self.device = self._get_device()
            
            # Move model to device
            if self.model:
                self.model.to(self.device)
                self.available = True
                print(f"✅ YOLO detector initialized on {self.device.upper()}")
            
        except Exception as e:
            print(f"❌ Failed to load YOLO model: {e}")
            print("   Will use MediaPipe fallback")
            self.model = None
            self.available = False
    
    def _get_device(self) -> str:
        """Detect available device"""
        try:
            import torch
            if torch.cuda.is_available():
                return 'cuda:0'
        except:
            pass
        return 'cpu'
    
    def is_available(self) -> bool:
        """Check if detector is ready to use"""
        return self.available and self.model is not None
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect faces in frame
        
        Args:
            frame: Input image (BGR)
        
        Returns:
            List of face dictionaries, empty list if detection fails
        """
        if not self.is_available():
            return []
        
        try:
            # Run detection
            results = self.model(frame, verbose=False, device=self.device)
            
            faces = []
            
            if results and len(results) > 0:
                result = results[0]
                
                if result.boxes is not None:
                    for box in result.boxes:
                        # Get class (0 = person for standard YOLO)
                        cls = int(box.cls[0])
                        
                        # If using person detection, only process person class
                        if self.use_person_detection and cls != 0:
                            continue
                        
                        # Get coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        x = int(x1)
                        y = int(y1)
                        w = int(x2 - x1)
                        h = int(y2 - y1)
                        
                        # If person detection, extract face region (upper 30% of body)
                        if self.use_person_detection:
                            face_h = int(h * 0.3)  # Top 30% of person
                            face_w = int(w * 0.8)  # 80% of person width
                            
                            # Center the face box
                            x = x + int(w * 0.1)
                            y = y + int(h * 0.05)  # Slight offset from top
                            w = face_w
                            h = face_h
                        
                        # Filter small faces
                        if w < MIN_FACE_SIZE or h < MIN_FACE_SIZE:
                            continue
                        
                        # Get confidence
                        conf = float(box.conf[0])
                        
                        faces.append({
                            'bbox': (x, y, w, h),
                            'confidence': conf,
                            'area': w * h,
                            'center': (x + w // 2, y + h // 2)
                        })
            
            # Sort by area (largest first)
            faces.sort(key=lambda f: f['area'], reverse=True)
            return faces
            
        except Exception as e:
            print(f"⚠️ YOLO detection error: {e}")
            return []
    
    def extract_face_region(self, frame: np.ndarray, bbox: Tuple[int, int, int, int], 
                           padding: float = 0.2) -> np.ndarray:
        """Extract face region with padding"""
        x, y, w, h = bbox
        
        pad_w = int(w * padding)
        pad_h = int(h * padding)
        
        x1 = max(0, x - pad_w)
        y1 = max(0, y - pad_h)
        x2 = min(frame.shape[1], x + w + pad_w)
        y2 = min(frame.shape[0], y + h + pad_h)
        
        return frame[y1:y2, x1:x2]
    
    def draw_face_box(self, frame: np.ndarray, face: Dict, 
                      color: Tuple[int, int, int], 
                      label: str = None, 
                      is_main: bool = False):
        """Draw bounding box around face"""
        x, y, w, h = face['bbox']
        
        thickness = 3 if is_main else 2
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
        
        if label:
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6 if is_main else 0.5
            font_thickness = 2 if is_main else 1
            
            (text_width, text_height), _ = cv2.getTextSize(
                label, font, font_scale, font_thickness
            )
            
            cv2.rectangle(frame, (x, y - text_height - 10),
                         (x + text_width + 10, y), color, -1)
            
            cv2.putText(frame, label, (x + 5, y - 5), font,
                       font_scale, (0, 0, 0), font_thickness)
    
    def apply_blur_to_face(self, frame: np.ndarray, bbox: Tuple[int, int, int, int], 
                          blur_strength: int = 51):
        """Apply blur to a face region"""
        x, y, w, h = bbox
        
        if blur_strength % 2 == 0:
            blur_strength += 1
        
        face_region = frame[y:y+h, x:x+w]
        
        if face_region.size > 0:
            blurred = cv2.GaussianBlur(face_region, (blur_strength, blur_strength), 0)
            frame[y:y+h, x:x+w] = blurred
    
    def close(self):
        """Release resources"""
        self.model = None
        self.available = False


# Test function
if __name__ == "__main__":
    print("Testing YOLO Face Detector...")
    print("="*60)
    
    detector = YOLOFaceDetector()
    
    if detector.is_available():
        print("\n✅ YOLO detector ready!")
        print(f"Device: {detector.device}")
        print(f"Person detection mode: {detector.use_person_detection}")
        
        # Test with webcam
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            print("\n📹 Testing with webcam (press 'q' to quit)...")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                faces = detector.detect_faces(frame)
                
                # Draw faces
                for i, face in enumerate(faces):
                    is_main = (i == 0)
                    color = (0, 255, 0) if is_main else (128, 128, 128)
                    label = f"Face {i+1} ({face['confidence']:.2f})"
                    detector.draw_face_box(frame, face, color, label, is_main)
                
                cv2.putText(frame, f"Faces: {len(faces)}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                cv2.imshow('YOLO Face Detection Test', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
        else:
            print("❌ Could not open webcam")
    
    else:
        print("\n❌ YOLO detector not available")
        print("This is normal - MediaPipe will be used instead")