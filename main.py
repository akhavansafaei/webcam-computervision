# File: main.py
"""
Smart Mirror - Main Application
EleComp Isfahan Exhibition

Usage:
    python main.py
"""

import cv2
import time
import numpy as np
from datetime import datetime
from pathlib import Path

# Import GPU configuration first
from src.gpu_config import print_device_info, GPU_CONFIG

# Import modules
from src import (
    db, FaceDetector, FaceAnalyzer, AIMessageGenerator,
    SessionManager, UIRenderer, validate_config
)
from src.database import db

# Try to import YOLO detector with fallback
YOLO_AVAILABLE = False
YOLOFaceDetector = None

if GPU_CONFIG['using_gpu']:
    try:
        from src.yolo_face_detector import YOLOFaceDetector as YOLODetector
        YOLOFaceDetector = YOLODetector
        print("📦 YOLO face detector module loaded")
    except ImportError as e:
        print(f"⚠️ YOLO import failed: {e}")
        print("⚠️ Will use MediaPipe instead")

from src.config import (
    CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT,
    ANALYSIS_INTERVAL, SIMILARITY_THRESHOLD,
    PHOTOS_DIR, SHOW_FPS, USE_YOLO_IF_GPU
)


class SmartMirror:
    """Main Smart Mirror application"""
    
    def __init__(self):
        print("\n" + "="*60)
        print("Smart Mirror - EleComp Isfahan")
        print("="*60 + "\n")
        
        # Show GPU configuration
        print_device_info()
        
        # Validate configuration
        validate_config()
        print()
        
        # Initialize face detector with intelligent fallback
        self.detector = self._initialize_detector()
        
        # Initialize other components
        self.analyzer = FaceAnalyzer()
        self.ai_generator = AIMessageGenerator()
        self.session_manager = SessionManager()
        self.ui_renderer = UIRenderer()
        
        # Camera
        self.camera = None
        self.init_camera()
        
        # FPS tracking
        self.fps = 0
        self.frame_count = 0
        self.fps_start_time = time.time()
        
        print("\n✅ Smart Mirror initialized successfully!\n")
    
    def _initialize_detector(self):
        """
        Initialize face detector with intelligent fallback
        Priority: YOLO (if GPU) → MediaPipe (always works)
        """
        detector_type = "MediaPipe (CPU)"
        
        # Try YOLO if GPU is available and enabled in config
        if GPU_CONFIG['using_gpu'] and USE_YOLO_IF_GPU and YOLOFaceDetector:
            try:
                print("🚀 Attempting to initialize YOLO face detector...")
                yolo_detector = YOLOFaceDetector(auto_download=True)
                
                if yolo_detector.is_available():
                    print("✅ Using YOLO face detector (GPU accelerated)")
                    detector_type = "YOLO (GPU)"
                    return yolo_detector
                else:
                    print("⚠️ YOLO initialization failed, falling back to MediaPipe")
                    
            except Exception as e:
                print(f"⚠️ YOLO error: {e}")
                print("⚠️ Falling back to MediaPipe")
        
        # Fallback to MediaPipe (always reliable)
        print("📦 Initializing MediaPipe face detector...")
        mediapipe_detector = FaceDetector()
        print(f"✅ Using {detector_type}")
        
        return mediapipe_detector
    
    def init_camera(self):
        """Initialize camera"""
        print(f"📷 Initializing camera {CAMERA_INDEX}...")
        
        self.camera = cv2.VideoCapture(CAMERA_INDEX)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        
        if not self.camera.isOpened():
            raise RuntimeError("❌ Failed to open camera!")
        
        print("✅ Camera initialized")
    
    def calculate_fps(self):
        """Calculate current FPS"""
        self.frame_count += 1
        
        if self.frame_count >= 30:
            elapsed = time.time() - self.fps_start_time
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_start_time = time.time()
    
    def process_frame(self, frame: np.ndarray):
        """
        Process single frame
        
        Args:
            frame: Input frame from camera
        
        Returns:
            Processed frame with UI
        """
        # Detect faces
        faces = self.detector.detect_faces(frame)
        
        if not faces:
            # No faces - cleanup expired sessions
            ended_sessions = self.session_manager.cleanup_sessions()
            
            # Get stats and render empty frame
            stats = db.get_statistics()
            return self.ui_renderer.render_frame(
                frame, None, None, None, stats, self.fps
            )
        
        # Get main face (largest/closest)
        main_face = faces[0]
        secondary_faces = faces[1:]
        
        # Blur secondary faces
        for face in secondary_faces:
            self.detector.apply_blur_to_face(frame, face['bbox'])
            self.detector.draw_face_box(frame, face, (128, 128, 128), 
                                       f"#{len(faces) - faces.index(face)}")
        
        # Extract main face region
        main_face_img = self.detector.extract_face_region(frame, main_face['bbox'])
        
        # Check if we should analyze
        # First, try to match with existing profiles using a quick embedding
        if main_face_img.size > 0:
            # Extract embedding
            embedding = self.analyzer.extract_embedding(main_face_img)
            
            # Find matching profile
            profile = db.find_profile_by_embedding(embedding, SIMILARITY_THRESHOLD)
            
            if profile:
                # Existing visitor
                profile_id = profile['id']
                
                # Start/resume session
                session = self.session_manager.start_session(profile_id, profile)
                
                # Check if should perform full analysis
                if self.session_manager.should_analyze(profile_id, ANALYSIS_INTERVAL):
                    print(f"🔍 Analyzing returning visitor (Profile {profile_id})...")
                    
                    # Perform full analysis
                    analysis = self.analyzer.analyze_face(main_face_img)
                    
                    # Update profile
                    db.update_profile(profile_id)
                    
                    # Build context for AI message
                    context = self.build_context(profile, analysis)
                    
                    # Generate AI message
                    ai_message = self.ai_generator.generate_message(context)
                    
                    # Save photo
                    photo_path = self.save_photo(main_face_img, profile_id)
                    
                    # Add record
                    db.add_record(profile_id, analysis, photo_path, ai_message)
                    
                    # Update session
                    self.session_manager.update_session(profile_id, analysis, ai_message)
                    
                    print(f"✅ Analysis complete | Message: {ai_message}")
                
            else:
                # New visitor
                print("🆕 New visitor detected! Creating profile...")
                
                # Perform full analysis
                analysis = self.analyzer.analyze_face(main_face_img)
                
                # Save photo
                photo_path = self.save_photo(main_face_img, profile_id=None)
                
                # Create profile
                profile_id = db.create_profile(embedding, analysis, photo_path)
                
                # Get profile data
                profile = db.get_profile(profile_id)
                
                # Build context
                context = self.build_context(profile, analysis)
                
                # Generate AI message
                ai_message = self.ai_generator.generate_message(context)
                
                # Add record
                db.add_record(profile_id, analysis, photo_path, ai_message)
                
                # Start session
                session = self.session_manager.start_session(profile_id, profile)
                self.session_manager.update_session(profile_id, analysis, ai_message)
                
                print(f"✅ Profile created (ID: {profile_id}) | Message: {ai_message}")
            
            # Draw main face box
            self.detector.draw_face_box(frame, main_face, (0, 255, 0), 
                                       "Main", is_main=True)
            
            # Render UI
            stats = db.get_statistics()
            rendered_frame = self.ui_renderer.render_frame(
                frame, main_face, secondary_faces, session, stats, self.fps
            )
            
            return rendered_frame
        
        # If face extraction failed, return original frame
        stats = db.get_statistics()
        return self.ui_renderer.render_frame(frame, None, None, None, stats, self.fps)
    
    def build_context(self, profile: dict, analysis: dict) -> dict:
        """Build context for AI message generation"""
        context = {
            'profile_id': profile['id'],
            'current': {
                'age': analysis.get('age'),
                'gender': analysis.get('dominant_gender'),
                'emotion': analysis.get('dominant_emotion')
            },
            'history': {
                'is_new': profile['total_visits'] == 1,
                'visit_number': profile['total_visits'],
                'first_seen': profile['first_seen'],
                'last_seen': profile['last_seen']
            }
        }
        
        # Add comparison if returning visitor
        if profile['total_visits'] > 1:
            previous_record = db.get_previous_record(profile['id'])
            if previous_record:
                context['comparison'] = {
                    'previous_emotion': previous_record['emotion'],
                    'emotion_changed': previous_record['emotion'] != analysis.get('dominant_emotion'),
                    'time_since_last': (
                        datetime.now() - datetime.fromisoformat(previous_record['timestamp'])
                    ).total_seconds()
                }
        
        return context
    
    def save_photo(self, face_img: np.ndarray, profile_id: int = None) -> str:
        """Save photo to disk"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if profile_id:
            filename = f"profile_{profile_id}_{timestamp}.jpg"
        else:
            filename = f"new_{timestamp}.jpg"
        
        filepath = PHOTOS_DIR / filename
        cv2.imwrite(str(filepath), face_img)
        
        return str(filepath)
    
    def run(self):
        """Main application loop"""
        print("\n🚀 Starting Smart Mirror...")
        print("Press 'q' to quit, 's' for statistics\n")
        
        try:
            while True:
                # Read frame
                ret, frame = self.camera.read()
                if not ret:
                    print("❌ Failed to read frame")
                    break
                
                # Calculate FPS
                self.calculate_fps()
                
                # Process frame
                processed_frame = self.process_frame(frame)
                
                # Display
                cv2.imshow('Smart Mirror - EleComp Isfahan', processed_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("\n👋 Quitting...")
                    break
                elif key == ord('s'):
                    self.print_statistics()
        
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.cleanup()
    
    def print_statistics(self):
        """Print current statistics"""
        stats = db.get_statistics()
        active_sessions = self.session_manager.get_active_count()
        
        print("\n" + "="*60)
        print("📊 Statistics")
        print("="*60)
        print(f"Total unique visitors: {stats['total_visitors']}")
        print(f"Today's visits: {stats['today_visits']}")
        print(f"Active sessions: {active_sessions}")
        print(f"Top emotion today: {stats['top_emotion']}")
        print(f"Current FPS: {self.fps:.1f}")
        print("="*60 + "\n")
    
    def cleanup(self):
        """Cleanup resources"""
        print("\n🧹 Cleaning up...")
        
        # Close camera
        if self.camera:
            self.camera.release()
        
        # Close OpenCV windows
        cv2.destroyAllWindows()
        
        # Clear sessions
        self.session_manager.clear_all()
        
        # Close face detector
        self.detector.close()
        
        print("✅ Cleanup complete")
        print("\n👋 Goodbye!\n")


def main():
    """Entry point"""
    try:
        app = SmartMirror()
        app.run()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())