# File: src\face_detector.py
"""
Fast face detection using MediaPipe
"""
import cv2
import mediapipe as mp
import numpy as np
from typing import List, Dict, Tuple
from src.config import MIN_DETECTION_CONFIDENCE, MIN_FACE_SIZE


class FaceDetector:
    """Fast face detection using MediaPipe"""
    
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize face detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0,  # 0 for close range, 1 for far range
            min_detection_confidence=MIN_DETECTION_CONFIDENCE
        )
        
        print("✅ Face detector initialized (MediaPipe)")
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect faces in frame
        
        Args:
            frame: Input image (BGR)
        
        Returns:
            List of face dictionaries with bbox, confidence, and area
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        results = self.face_detection.process(rgb_frame)
        
        faces = []
        
        if results.detections:
            h, w, _ = frame.shape
            
            for detection in results.detections:
                # Get bounding box
                bbox = detection.location_data.relative_bounding_box
                
                # Convert to absolute coordinates
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                # Ensure coordinates are within frame
                x = max(0, x)
                y = max(0, y)
                width = min(width, w - x)
                height = min(height, h - y)
                
                # Filter small faces
                if width < MIN_FACE_SIZE or height < MIN_FACE_SIZE:
                    continue
                
                # Calculate area (for sorting)
                area = width * height
                
                # Get confidence score
                confidence = detection.score[0]
                
                faces.append({
                    'bbox': (x, y, width, height),
                    'confidence': confidence,
                    'area': area,
                    'center': (x + width // 2, y + height // 2)
                })
        
        # Sort by area (largest first - closest face)
        faces.sort(key=lambda f: f['area'], reverse=True)
        
        return faces
    
    def extract_face_region(self, frame: np.ndarray, bbox: Tuple[int, int, int, int], 
                           padding: float = 0.2) -> np.ndarray:
        """
        Extract face region with padding
        
        Args:
            frame: Input image
            bbox: Bounding box (x, y, w, h)
            padding: Padding ratio (0.2 = 20% padding)
        
        Returns:
            Cropped face image
        """
        x, y, w, h = bbox
        
        # Add padding
        pad_w = int(w * padding)
        pad_h = int(h * padding)
        
        x1 = max(0, x - pad_w)
        y1 = max(0, y - pad_h)
        x2 = min(frame.shape[1], x + w + pad_w)
        y2 = min(frame.shape[0], y + h + pad_h)
        
        # Extract region
        face_region = frame[y1:y2, x1:x2]
        
        return face_region
    
    def draw_face_box(self, frame: np.ndarray, face: Dict, 
                      color: Tuple[int, int, int], 
                      label: str = None, 
                      is_main: bool = False):
        """
        Draw bounding box around face
        
        Args:
            frame: Image to draw on
            face: Face dictionary
            color: Box color (BGR)
            label: Optional text label
            is_main: Whether this is the main focused face
        """
        x, y, w, h = face['bbox']
        
        # Draw rectangle
        thickness = 3 if is_main else 2
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
        
        # Draw label if provided
        if label:
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6 if is_main else 0.5
            font_thickness = 2 if is_main else 1
            
            # Get text size for background
            (text_width, text_height), baseline = cv2.getTextSize(
                label, font, font_scale, font_thickness
            )
            
            # Draw background rectangle
            cv2.rectangle(
                frame,
                (x, y - text_height - 10),
                (x + text_width + 10, y),
                color,
                -1
            )
            
            # Draw text
            cv2.putText(
                frame,
                label,
                (x + 5, y - 5),
                font,
                font_scale,
                (0, 0, 0),  # Black text
                font_thickness
            )
    
    def apply_blur_to_face(self, frame: np.ndarray, bbox: Tuple[int, int, int, int], 
                          blur_strength: int = 51):
        """
        Apply blur to a face region
        
        Args:
            frame: Image to blur (modified in place)
            bbox: Bounding box (x, y, w, h)
            blur_strength: Blur kernel size (must be odd)
        """
        x, y, w, h = bbox
        
        # Ensure blur strength is odd
        if blur_strength % 2 == 0:
            blur_strength += 1
        
        # Extract face region
        face_region = frame[y:y+h, x:x+w]
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(face_region, (blur_strength, blur_strength), 0)
        
        # Replace region with blurred version
        frame[y:y+h, x:x+w] = blurred
    
    def close(self):
        """Release resources"""
        self.face_detection.close()
        print("Face detector closed")


# Test function
if __name__ == "__main__":
    detector = FaceDetector()
    
    # Test with webcam
    cap = cv2.VideoCapture(0)
    
    print("Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        faces = detector.detect_faces(frame)
        
        # Draw all faces
        for i, face in enumerate(faces):
            is_main = (i == 0)  # First face is main
            color = (0, 255, 0) if is_main else (128, 128, 128)
            label = f"Main ({face['confidence']:.2f})" if is_main else f"#{i+1}"
            
            if is_main:
                detector.draw_face_box(frame, face, color, label, is_main=True)
            else:
                # Blur secondary faces
                detector.apply_blur_to_face(frame, face['bbox'])
                detector.draw_face_box(frame, face, color, label, is_main=False)
        
        # Show count
        cv2.putText(frame, f"Faces: {len(faces)}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow('Face Detection Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    detector.close()