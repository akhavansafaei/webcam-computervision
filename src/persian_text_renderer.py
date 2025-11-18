# File: src\persian_text_renderer.py
"""
Persian text renderer using PIL for OpenCV
Handles right-to-left text and Persian character shaping
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display


class PersianTextRenderer:
    """Render Persian/Arabic text on OpenCV images"""
    
    def __init__(self):
        """Initialize with default font"""
        self.default_font_size = 32
        self.font = None
        self.load_font()
    
    def load_font(self, font_path: str = None, size: int = None):
        """
        Load a font for rendering
        
        Args:
            font_path: Path to TTF font file (None = use default)
            size: Font size in pixels
        """
        size = size or self.default_font_size
        
        try:
            if font_path:
                # Load custom font
                self.font = ImageFont.truetype(font_path, size)
            else:
                # Try to load system fonts
                font_paths = [
                    # Windows fonts
                    r"C:\Windows\Fonts\arial.ttf",
                    r"C:\Windows\Fonts\tahoma.ttf",
                    r"C:\Windows\Fonts\B Nazanin.ttf",
                    # Linux fonts
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    # Mac fonts
                    "/System/Library/Fonts/Supplemental/Arial.ttf",
                ]
                
                for path in font_paths:
                    try:
                        self.font = ImageFont.truetype(path, size)
                        print(f"Loaded font: {path}")
                        break
                    except:
                        continue
                
                if not self.font:
                    # Fallback to default font
                    self.font = ImageFont.load_default()
                    print("Warning: Using default font (limited Persian support)")
        
        except Exception as e:
            print(f"Warning: Font loading error: {e}")
            self.font = ImageFont.load_default()
    
    def reshape_persian_text(self, text: str) -> str:
        """
        Reshape Persian text for proper display
        
        Args:
            text: Input Persian text
        
        Returns:
            Reshaped text ready for display
        """
        # Reshape Arabic/Persian characters
        reshaped_text = arabic_reshaper.reshape(text)
        
        # Convert to display order (right-to-left)
        bidi_text = get_display(reshaped_text)
        
        return bidi_text
    
    def get_text_size(self, text: str, font_size: int = None) -> tuple:
        """
        Get the size of rendered text
        
        Args:
            text: Text to measure
            font_size: Font size (None = use default)
        
        Returns:
            (width, height) tuple
        """
        if font_size and font_size != self.default_font_size:
            self.load_font(size=font_size)
        
        # Reshape text
        display_text = self.reshape_persian_text(text)
        
        # Get bounding box
        bbox = self.font.getbbox(display_text)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        return (width, height)
    
    def put_text(self, img: np.ndarray, text: str, position: tuple,
                 font_size: int = 32, color: tuple = (255, 255, 255),
                 bg_color: tuple = None, padding: int = 5) -> np.ndarray:
        """
        Put Persian text on OpenCV image
        
        Args:
            img: OpenCV image (BGR)
            text: Persian text to render
            position: (x, y) position (top-left corner)
            font_size: Font size in pixels
            color: Text color (R, G, B)
            bg_color: Background color (R, G, B) or None for transparent
            padding: Padding around text if bg_color is set
        
        Returns:
            Modified image
        """
        # Load font with correct size
        if font_size != self.default_font_size:
            self.load_font(size=font_size)
        
        # Reshape Persian text
        display_text = self.reshape_persian_text(text)
        
        # Convert OpenCV BGR to PIL RGB
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        
        x, y = position
        
        # Draw background if specified
        if bg_color:
            bbox = self.font.getbbox(display_text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            bg_box = [
                x - padding,
                y - padding,
                x + text_width + padding,
                y + text_height + padding
            ]
            draw.rectangle(bg_box, fill=bg_color)
        
        # Draw text
        draw.text((x, y), display_text, font=self.font, fill=color)
        
        # Convert back to OpenCV BGR
        img_with_text = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        return img_with_text
    
    def put_text_centered(self, img: np.ndarray, text: str, y: int,
                         font_size: int = 32, color: tuple = (255, 255, 255),
                         bg_color: tuple = None) -> np.ndarray:
        """
        Put centered Persian text on image
        
        Args:
            img: OpenCV image
            text: Text to render
            y: Y position (vertical center)
            font_size: Font size
            color: Text color (R, G, B)
            bg_color: Background color or None
        
        Returns:
            Modified image
        """
        # Get text size
        if font_size != self.default_font_size:
            self.load_font(size=font_size)
        
        width, height = self.get_text_size(text, font_size)
        
        # Calculate centered X position
        img_width = img.shape[1]
        x = (img_width - width) // 2
        
        return self.put_text(img, text, (x, y), font_size, color, bg_color)


# Global instance
persian_renderer = PersianTextRenderer()


# Convenience functions
def put_persian_text(img, text, position, font_size=32, color=(255, 255, 255), bg_color=None):
    """Convenience function to put Persian text"""
    return persian_renderer.put_text(img, text, position, font_size, color, bg_color)


def put_persian_text_centered(img, text, y, font_size=32, color=(255, 255, 255), bg_color=None):
    """Convenience function to put centered Persian text"""
    return persian_renderer.put_text_centered(img, text, y, font_size, color, bg_color)


# Test function
if __name__ == "__main__":
    # Create test image
    img = np.zeros((400, 800, 3), dtype=np.uint8)
    
    # Test texts
    texts = [
        "سلام! خوش آمدید",
        "آیینه هوشمند الکامپ",
        "این یک تست متن فارسی است",
        "123 عدد انگلیسی ABC"
    ]
    
    renderer = PersianTextRenderer()
    
    y = 50
    for text in texts:
        img = renderer.put_text(
            img, text, (50, y),
            font_size=32,
            color=(255, 255, 255),
            bg_color=(50, 50, 50),
            padding=5
        )
        y += 80
    
    # Display
    cv2.imshow('Persian Text Test', img)
    print("Press any key to close...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("Test complete!")