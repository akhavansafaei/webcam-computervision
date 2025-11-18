# File: src\__init__.py
"""
Smart Mirror - EleComp Isfahan Exhibition
Main package initialization
"""

__version__ = "1.0.0"
__author__ = "Smart Mirror Team"
__description__ = "AI-powered smart mirror for visitor interaction"

from src.config import validate_config
from src.database import db
from src.face_detector import FaceDetector
from src.face_analyzer import FaceAnalyzer
from src.ai_message_generator import AIMessageGenerator
from src.session_manager import SessionManager
from src.ui_renderer import UIRenderer

__all__ = [
    'db',
    'FaceDetector',
    'FaceAnalyzer',
    'AIMessageGenerator',
    'SessionManager',
    'UIRenderer',
    'validate_config'
]