# File: src/face_analyzer.py
"""
Face analysis using DeepFace (age, gender, emotion, embedding)
With configurable features for performance optimization
"""
import cv2
import numpy as np
from typing import Dict, Tuple
from deepface import DeepFace
from src.config import (
    DEEPFACE_MODEL, DEEPFACE_DETECTOR,
    ANALYZE_AGE, ANALYZE_GENDER, ANALYZE_EMOTION,
    ENABLE_ANALYSIS
)

# Import GPU configuration
from src.gpu_config import GPU_CONFIG


class FaceAnalyzer:
    """Face analysis using DeepFace"""
    
    def __init__(self):
        self.model_name = DEEPFACE_MODEL
        self.detector_backend = DEEPFACE_DETECTOR
        
        # Feature flags
        self.analyze_age = ANALYZE_AGE
        self.analyze_gender = ANALYZE_GENDER
        self.analyze_emotion = ANALYZE_EMOTION
        self.enable_analysis = ENABLE_ANALYSIS
        
        # Show GPU status
        device = GPU_CONFIG['device']
        print(f"👤 Face analyzer initializing...")
        print(f"   Device: {device}")
        
        # Show enabled features
        if self.enable_analysis:
            features = []
            if self.analyze_age:
                features.append("Age")
            if self.analyze_gender:
                features.append("Gender")
            if self.analyze_emotion:
                features.append("Emotion")
            
            if features:
                print(f"   Features: {', '.join(features)}")
            else:
                print(f"   Features: None (only embedding)")
        else:
            print(f"   Analysis: Disabled (max speed mode)")
        
        # Warm up models (download if needed)
        if self.enable_analysis and (self.analyze_age or self.analyze_gender or self.analyze_emotion):
            print("   Loading models (first time may take a while)...")
            self._warmup()
        
        print("✅ Face analyzer initialized")
    
    def _warmup(self):
        """Warm up models by running a dummy analysis"""
        try:
            # Create a dummy face image
            dummy_img = np.zeros((160, 160, 3), dtype=np.uint8)
            
            # Build actions list based on enabled features
            actions = []
            if self.analyze_age:
                actions.append('age')
            if self.analyze_gender:
                actions.append('gender')
            if self.analyze_emotion:
                actions.append('emotion')
            
            if actions:
                # Run analysis to download models
                DeepFace.analyze(
                    dummy_img,
                    actions=actions,
                    enforce_detection=False,
                    detector_backend=self.detector_backend,
                    silent=True
                )
            
            # Load embedding model (always needed)
            DeepFace.represent(
                dummy_img,
                model_name=self.model_name,
                enforce_detection=False,
                detector_backend=self.detector_backend
            )
            
        except Exception as e:
            print(f"   ⚠️  Warmup warning (safe to ignore): {e}")
    
    def analyze_face(self, face_img: np.ndarray) -> Dict:
        """
        Analyze face for enabled features
        
        Args:
            face_img: Face image (BGR)
        
        Returns:
            Dictionary with analysis results (only enabled features)
        """
        # If analysis disabled, return defaults
        if not self.enable_analysis:
            return self._get_default_analysis()
        
        try:
            # Build actions list
            actions = []
            if self.analyze_age:
                actions.append('age')
            if self.analyze_gender:
                actions.append('gender')
            if self.analyze_emotion:
                actions.append('emotion')
            
            # If no features enabled, return defaults
            if not actions:
                return self._get_default_analysis()
            
            # Run analysis
            result = DeepFace.analyze(
                face_img,
                actions=actions,
                enforce_detection=False,
                detector_backend=self.detector_backend,
                silent=True
            )
            
            # DeepFace returns a list, take first result
            if isinstance(result, list):
                result = result[0]
            
            # Build result dict with only enabled features
            analysis = {}
            
            if self.analyze_age:
                analysis['age'] = result.get('age', 25)
            else:
                analysis['age'] = 25  # Default
            
            if self.analyze_gender:
                analysis['gender'] = result.get('gender', {})
                analysis['dominant_gender'] = result.get('dominant_gender', 'Man')
            else:
                analysis['gender'] = {'Woman': 50.0, 'Man': 50.0}
                analysis['dominant_gender'] = 'Man'
            
            if self.analyze_emotion:
                analysis['emotion'] = result.get('emotion', {})
                analysis['dominant_emotion'] = result.get('dominant_emotion', 'neutral')
            else:
                analysis['emotion'] = {'neutral': 100}
                analysis['dominant_emotion'] = 'neutral'
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Analysis error: {e}")
            return self._get_default_analysis()
    
    def extract_embedding(self, face_img: np.ndarray) -> np.ndarray:
        """
        Extract face embedding vector
        
        Args:
            face_img: Face image (BGR)
        
        Returns:
            Embedding vector (128D for Facenet)
        """
        try:
            embedding_obj = DeepFace.represent(
                face_img,
                model_name=self.model_name,
                enforce_detection=False,
                detector_backend=self.detector_backend
            )
            
            # DeepFace returns a list of dicts
            if isinstance(embedding_obj, list):
                embedding = embedding_obj[0]['embedding']
            else:
                embedding = embedding_obj['embedding']
            
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            print(f"⚠️ Embedding error: {e}")
            # Return zero vector as fallback
            return np.zeros(128, dtype=np.float32)
    
    def analyze_with_embedding(self, face_img: np.ndarray) -> Tuple[Dict, np.ndarray]:
        """
        Perform both analysis and embedding extraction
        
        Args:
            face_img: Face image (BGR)
        
        Returns:
            Tuple of (analysis_dict, embedding_vector)
        """
        analysis = self.analyze_face(face_img)
        embedding = self.extract_embedding(face_img)
        
        return analysis, embedding
    
    def _get_default_analysis(self) -> Dict:
        """Return default analysis when detection fails or disabled"""
        return {
            'age': 25,
            'gender': {'Woman': 50.0, 'Man': 50.0},
            'dominant_gender': 'Man',
            'emotion': {
                'angry': 0, 'disgust': 0, 'fear': 0,
                'happy': 0, 'sad': 0, 'surprise': 0, 'neutral': 100
            },
            'dominant_emotion': 'neutral'
        }
    
    def get_emotion_emoji(self, emotion: str) -> str:
        """Get emoji for emotion"""
        emoji_map = {
            'happy': '😊',
            'sad': '😢',
            'angry': '😠',
            'surprise': '😲',
            'fear': '😨',
            'neutral': '😐',
            'disgust': '🤢'
        }
        return emoji_map.get(emotion, '😐')
    
    def format_analysis_text(self, analysis: Dict) -> str:
        """Format analysis as readable text (only enabled features)"""
        parts = []
        
        # Age (if enabled)
        if self.analyze_age:
            age = analysis.get('age', 'N/A')
            parts.append(f"{age} ساله")
        
        # Gender (if enabled)
        if self.analyze_gender:
            gender = analysis.get('dominant_gender', 'N/A')
            from src.config import GENDER_TRANSLATIONS
            gender_fa = GENDER_TRANSLATIONS.get(gender, gender)
            parts.append(gender_fa)
        
        # Emotion (if enabled)
        if self.analyze_emotion:
            emotion = analysis.get('dominant_emotion', 'neutral')
            from src.config import EMOTION_TRANSLATIONS
            emotion_fa = EMOTION_TRANSLATIONS.get(emotion, emotion)
            parts.append(emotion_fa)
        
        return " | ".join(parts) if parts else "مهمان"


# Test function
if __name__ == "__main__":
    analyzer = FaceAnalyzer()
    
    # Test with webcam
    cap = cv2.VideoCapture(0)
    
    print("\n📹 Press 'q' to quit, 's' to analyze")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        cv2.imshow('Face Analyzer Test - Press S to analyze', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('s'):
            print("\n🔍 Analyzing...")
            
            # Analyze frame
            analysis, embedding = analyzer.analyze_with_embedding(frame)
            
            print(f"Age: {analysis.get('age', 'N/A')} (enabled: {analyzer.analyze_age})")
            print(f"Gender: {analysis.get('dominant_gender', 'N/A')} (enabled: {analyzer.analyze_gender})")
            print(f"Emotion: {analysis.get('dominant_emotion', 'N/A')} (enabled: {analyzer.analyze_emotion})")
            print(f"Embedding shape: {embedding.shape}")
            print(f"Formatted: {analyzer.format_analysis_text(analysis)}")
    
    cap.release()
    cv2.destroyAllWindows()