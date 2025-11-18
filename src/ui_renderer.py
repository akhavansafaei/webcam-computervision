# File: src\ui_renderer.py
"""
UI rendering module for Smart Mirror display
"""
import cv2
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime
from src.config import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT, COLOR_BACKGROUND,
    FONT_FACE, FONT_SCALE_LARGE, FONT_SCALE_MEDIUM, FONT_SCALE_SMALL,
    FONT_THICKNESS, EMOTION_TRANSLATIONS, GENDER_TRANSLATIONS,
    DISPLAY_WIDTH, DISPLAY_HEIGHT
)
from src.persian_text_renderer import PersianTextRenderer


class UIRenderer:
    """Render UI elements on frame"""
    
    def __init__(self):
        self.font = FONT_FACE
        self.message_start_time = None
        self.current_message = ""
        self.message_display_chars = 0
        self.typing_speed = 0.05  # seconds per character
        
        # Persian text renderer
        self.persian_renderer = PersianTextRenderer()
        
        print("UI renderer initialized")
    
    def render_frame(self, frame: np.ndarray, main_face: Optional[Dict] = None,
                    secondary_faces: list = None, session: Optional[Dict] = None,
                    stats: Optional[Dict] = None, fps: float = 0) -> np.ndarray:
        """
        Render complete UI on frame
        
        Args:
            frame: Input frame
            main_face: Main face data
            secondary_faces: List of secondary faces
            session: Active session data
            stats: Statistics
            fps: Current FPS
        
        Returns:
            Rendered frame
        """
        # Create overlay
        overlay = frame.copy()
        
        # Draw header
        self._draw_header(overlay, fps)
        
        # Draw main face info box
        if main_face and session:
            self._draw_main_face_box(overlay, main_face, session)
        
        # Draw secondary faces count
        if secondary_faces:
            self._draw_secondary_faces_info(overlay, len(secondary_faces))
        
        # Draw AI message
        if session and session.get('ai_message'):
            self._draw_ai_message(overlay, session['ai_message'])
        
        # Draw footer with stats
        if stats:
            self._draw_footer(overlay, stats)
        
        return overlay
    
    def _draw_header(self, frame: np.ndarray, fps: float):
        """Draw header bar"""
        h, w = frame.shape[:2]
        
        # Semi-transparent background
        cv2.rectangle(frame, (0, 0), (w, 60), COLOR_BACKGROUND, -1)
        
        # Title
        title = "آیینه هوشمند الکامپ اصفهان 🎥"
        self._draw_persian_text(frame, title, (w // 2, 35), 
                               FONT_SCALE_LARGE, COLOR_PRIMARY, center=True)
        
        # FPS
        if fps > 0:
            fps_text = f"FPS: {fps:.1f}"
            cv2.putText(frame, fps_text, (w - 120, 40),
                       self.font, FONT_SCALE_SMALL, COLOR_SECONDARY, 1)
    
    def _draw_main_face_box(self, frame: np.ndarray, face: Dict, session: Dict):
        """Draw info box for main face"""
        x, y, w, h = face['bbox']
        
        # Get session data
        profile_data = session.get('profile_data', {})
        analysis = session.get('current_analysis', {})
        
        if not analysis:
            return
        
        # Prepare text
        visitor_num = profile_data.get('id', 0)
        age = analysis.get('age', 'N/A')
        gender = analysis.get('dominant_gender', 'N/A')
        emotion = analysis.get('dominant_emotion', 'neutral')
        visit_count = profile_data.get('total_visits', 1)
        
        gender_fa = GENDER_TRANSLATIONS.get(gender, gender)
        emotion_fa = EMOTION_TRANSLATIONS.get(emotion, emotion)
        
        # Info box position (to the right of face)
        box_x = x + w + 20
        box_y = y
        box_width = 300
        box_height = 200
        
        # Adjust if goes off screen
        if box_x + box_width > frame.shape[1]:
            box_x = max(0, x - box_width - 20)
        
        # Draw semi-transparent background
        self._draw_rounded_rect(frame, (box_x, box_y), (box_width, box_height),
                               COLOR_BACKGROUND, alpha=0.8)
        
        # Draw border
        cv2.rectangle(frame, (box_x, box_y), 
                     (box_x + box_width, box_y + box_height),
                     COLOR_PRIMARY, 2)
        
        # Draw text
        text_x = box_x + 15
        text_y = box_y + 40
        line_height = 35
        
        lines = [
            f"مهمان #{visitor_num}",
            f"سن: {age} ساله",
            f"جنسیت: {gender_fa}",
            f"احساس: {emotion_fa}",
            #f"بازدید: {visit_count} بار"
        ]
        
        for i, line in enumerate(lines):
            self._draw_persian_text(frame, line, (text_x, text_y + i * line_height),
                                   FONT_SCALE_MEDIUM, COLOR_TEXT)
    
    def _draw_secondary_faces_info(self, frame: np.ndarray, count: int):
        """Draw secondary faces count"""
        h, w = frame.shape[:2]
        
        text = f"افراد تشخیص داده شده: {count + 1} نفر"
        self._draw_persian_text(frame, text, (w // 2, h - 100),
                               FONT_SCALE_MEDIUM, COLOR_SECONDARY, center=True)
    
    def _draw_ai_message(self, frame: np.ndarray, message: str):
        """Draw AI generated message with typing animation"""
        h, w = frame.shape[:2]
        
        # Initialize typing animation
        if message != self.current_message:
            self.current_message = message
            self.message_start_time = datetime.now()
            self.message_display_chars = 0
        
        # Calculate how many characters to show
        if self.message_start_time:
            elapsed = (datetime.now() - self.message_start_time).total_seconds()
            self.message_display_chars = min(
                len(message),
                int(elapsed / self.typing_speed)
            )
        
        displayed_text = message[:self.message_display_chars]
        
        # Message box dimensions
        box_width = min(800, w - 100)
        box_height = 120
        box_x = (w - box_width) // 2
        box_y = h - box_height - 80
        
        # Draw semi-transparent background
        self._draw_rounded_rect(frame, (box_x, box_y), (box_width, box_height),
                               (50, 50, 50), alpha=0.9)
        
        # Draw border
        cv2.rectangle(frame, (box_x, box_y),
                     (box_x + box_width, box_y + box_height),
                     COLOR_PRIMARY, 2)
        
        # Draw icon
        icon_text = "💬"
        cv2.putText(frame, icon_text, (box_x + 15, box_y + 35),
                   self.font, FONT_SCALE_MEDIUM, COLOR_PRIMARY, 2)
        
        # Draw message text (wrapped)
        text_x = box_x + 70
        text_y = box_y + 40
        
        # Simple text wrapping
        words = displayed_text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if len(test_line) < 40:  # Approximate character limit
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Draw lines
        for i, line in enumerate(lines[:3]):  # Max 3 lines
            self._draw_persian_text(frame, line, (text_x, text_y + i * 30),
                                   FONT_SCALE_MEDIUM, COLOR_TEXT)
    
    def _draw_footer(self, frame: np.ndarray, stats: Dict):
        """Draw footer with statistics"""
        h, w = frame.shape[:2]
        
        # Semi-transparent background
        cv2.rectangle(frame, (0, h - 50), (w, h), COLOR_BACKGROUND, -1)
        
        # Stats text
        total = stats.get('total_visitors', 0)
        today = stats.get('today_visits', 0)
        
        stats_text = f"امروز: {today} نفر  |  کل: {total} بازدیدکننده"
        self._draw_persian_text(frame, stats_text, (w // 2, h - 20),
                               FONT_SCALE_MEDIUM, COLOR_TEXT, center=True)
    
    def _draw_persian_text(self, frame: np.ndarray, text: str, 
                          position: Tuple[int, int], scale: float,
                          color: Tuple[int, int, int], center: bool = False):
        """
        Draw Persian text using PIL-based renderer
        """
        # Convert scale to font size (approximate)
        font_size = int(scale * 30)
        
        # Convert BGR to RGB for color
        rgb_color = (color[2], color[1], color[0])
        
        if center:
            # Get text size and calculate centered position
            text_width, text_height = self.persian_renderer.get_text_size(text, font_size)
            x = position[0] - text_width // 2
            y = position[1] - text_height // 2
        else:
            x, y = position
        
        # Render text
        try:
            frame_with_text = self.persian_renderer.put_text(
                frame, text, (x, y), font_size, rgb_color
            )
            # Copy back to original frame
            frame[:] = frame_with_text
        except Exception as e:
            # Fallback to English/numbers only
            cv2.putText(frame, text, (x, y), self.font, scale, color, FONT_THICKNESS)
    
    def _draw_rounded_rect(self, frame: np.ndarray, position: Tuple[int, int],
                          size: Tuple[int, int], color: Tuple[int, int, int],
                          alpha: float = 0.7, radius: int = 10):
        """Draw rounded rectangle with transparency"""
        x, y = position
        w, h = size
        
        # Create overlay
        overlay = frame.copy()
        
        # Draw rounded rectangle (simplified - just rectangle for now)
        cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
        
        # Blend with original
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    def reset_message(self):
        """Reset message animation"""
        self.current_message = ""
        self.message_start_time = None
        self.message_display_chars = 0


# Test
if __name__ == "__main__":
    renderer = UIRenderer()
    
    # Create test frame
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    # Test data
    main_face = {
        'bbox': (300, 150, 200, 250)
    }
    
    session = {
        'profile_data': {'id': 42, 'total_visits': 3},
        'current_analysis': {
            'age': 28,
            'dominant_gender': 'Woman',
            'dominant_emotion': 'happy'
        },
        'ai_message': 'سلام! خوش اومدید به نمایشگاه الکامپ 😊'
    }
    
    stats = {
        'total_visitors': 247,
        'today_visits': 42
    }
    
    # Render
    rendered = renderer.render_frame(frame, main_face, [], session, stats, 30.5)
    
    # Display
    cv2.imshow('UI Test', rendered)
    cv2.waitKey(5000)
    cv2.destroyAllWindows()