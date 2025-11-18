# File: src/config.py
"""
Configuration module - reads from config.yaml and .env
"""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (for API keys)
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
CONFIG_FILE = BASE_DIR / "config.yaml"
DATA_DIR = BASE_DIR / "data"
PHOTOS_DIR = DATA_DIR / "photos"
CACHE_DIR = DATA_DIR / "cache"
MODELS_DIR = BASE_DIR / "models"

# Create directories
for directory in [DATA_DIR, PHOTOS_DIR, CACHE_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Load YAML configuration
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# OpenAI Configuration (from .env for security)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = config['openai']['model']
OPENAI_TEMPERATURE = config['openai']['temperature']
OPENAI_MAX_TOKENS = config['openai']['max_tokens']

# AI Message Settings
AI_MESSAGE_ENABLED = config['ai_message']['enabled']
AI_MESSAGE_USE_CACHE = config['ai_message']['use_cache']
STATIC_MESSAGES = config['ai_message']['static_messages']

# Camera Configuration
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", config['camera']['index']))
CAMERA_WIDTH = config['camera']['width']
CAMERA_HEIGHT = config['camera']['height']
CAMERA_FPS = config['camera']['fps']

# Face Detection Settings
MIN_DETECTION_CONFIDENCE = config['face_detection']['min_confidence']
MIN_FACE_SIZE = config['face_detection']['min_face_size']
USE_YOLO_IF_GPU = config['face_detection']['use_yolo_if_gpu']
FRAME_SKIP = config['face_detection'].get('frame_skip', 1)

# Face Analysis Settings
ANALYZE_AGE = config['face_analysis']['analyze_age']
ANALYZE_GENDER = config['face_analysis']['analyze_gender']
ANALYZE_EMOTION = config['face_analysis']['analyze_emotion']
ANALYSIS_INTERVAL = config['face_analysis']['analysis_interval']
SIMILARITY_THRESHOLD = config['face_analysis']['similarity_threshold']
DEEPFACE_MODEL = config['face_analysis']['model']
DEEPFACE_DETECTOR = config['face_analysis']['detector_backend']
ANALYSIS_USE_GPU = config['face_analysis'].get('use_gpu', True)
ENABLE_ANALYSIS = config['face_analysis'].get('enable_analysis', True)

# Session Management
SESSION_TIMEOUT = config['session']['timeout']

# Database
DATABASE_PATH = str(DATA_DIR / "database.db")

# UI Settings
DISPLAY_WIDTH = config['ui']['display_width']
DISPLAY_HEIGHT = config['ui']['display_height']
MESSAGE_DURATION = config['ui']['message_duration']
SHOW_FPS = config['ui']['show_fps']
SHOW_SECONDARY_FACES = config['ui'].get('show_secondary_faces', True)

# Colors (BGR)
COLOR_PRIMARY = tuple(config['colors']['primary'])
COLOR_SECONDARY = tuple(config['colors']['secondary'])
COLOR_BACKGROUND = tuple(config['colors']['background'])
COLOR_TEXT = tuple(config['colors']['text'])
COLOR_BLUR_BOX = tuple(config['colors']['blur_box'])

# Fonts
FONT_FACE = config['fonts']['face']
FONT_SCALE_LARGE = config['fonts']['scale_large']
FONT_SCALE_MEDIUM = config['fonts']['scale_medium']
FONT_SCALE_SMALL = config['fonts']['scale_small']
FONT_THICKNESS = config['fonts']['thickness']

# Translations
EMOTION_TRANSLATIONS = config['emotions']
GENDER_TRANSLATIONS = config['genders']

# AI Prompts
PROMPTS = config['prompts']
HAFEZ_POEMS = config['hafez_poems']

# Debug Mode
DEBUG = os.getenv("DEBUG", str(config['debug'])).lower() == "true"

def validate_config():
    """Validate configuration"""
    print("="*60)
    print("Configuration Summary")
    print("="*60)
    
    # Camera
    print(f"📷 Camera: {CAMERA_WIDTH}x{CAMERA_HEIGHT} @ {CAMERA_FPS} FPS")
    
    # Face Detection
    detector = "YOLO (GPU)" if USE_YOLO_IF_GPU else "MediaPipe (CPU)"
    print(f"👁️  Face Detection: {detector}")
    if FRAME_SKIP > 1:
        print(f"   Frame Skip: Every {FRAME_SKIP} frames (faster!)")
    
    # Face Analysis
    if ENABLE_ANALYSIS:
        features = []
        if ANALYZE_AGE:
            features.append("Age")
        if ANALYZE_GENDER:
            features.append("Gender")
        if ANALYZE_EMOTION:
            features.append("Emotion")
        
        if features:
            print(f"🧠 Analysis: {', '.join(features)}")
            print(f"   Interval: {ANALYSIS_INTERVAL}s")
            device = "GPU" if ANALYSIS_USE_GPU else "CPU"
            print(f"   Device: {device}")
        else:
            print("🧠 Analysis: Disabled (all features off)")
    else:
        print("🧠 Analysis: Disabled (max speed mode)")
    
    # AI Messages
    if AI_MESSAGE_ENABLED:
        print("💬 AI Messages: ENABLED (using LLM)")
        if not OPENAI_API_KEY:
            print("   ⚠️  Warning: OPENAI_API_KEY not set")
    else:
        print("💬 AI Messages: DISABLED (using static messages)")
    
    # UI
    if not SHOW_SECONDARY_FACES:
        print("🎨 UI: Simplified (secondary faces hidden)")
    
    # Memory Estimate
    estimated_memory = 500  # Base
    if USE_YOLO_IF_GPU:
        estimated_memory += 1500
    if ANALYZE_AGE:
        estimated_memory += 300
    if ANALYZE_GENDER:
        estimated_memory += 200
    if ANALYZE_EMOTION:
        estimated_memory += 400
    
    print(f"💾 Estimated GPU Memory: ~{estimated_memory}MB")
    
    # Performance estimate
    if CAMERA_WIDTH <= 320 and FRAME_SKIP >= 2 and not USE_YOLO_IF_GPU:
        print("⚡ Expected Performance: 35-45 FPS (Very Fast)")
    elif CAMERA_WIDTH <= 480 and not USE_YOLO_IF_GPU:
        print("⚡ Expected Performance: 25-35 FPS (Fast)")
    else:
        print("⚡ Expected Performance: 15-25 FPS (Moderate)")
    
    print("="*60)
    
    if DEBUG:
        print("⚠️  Debug mode enabled")

if __name__ == "__main__":
    validate_config()