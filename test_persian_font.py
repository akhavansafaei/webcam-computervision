# File: test_persian_font.py
"""
Test Persian font rendering
Run this to verify Persian text displays correctly
"""
import cv2
import numpy as np
from src.persian_text_renderer import PersianTextRenderer

print("🧪 Testing Persian Font Rendering\n")

# Create renderer
renderer = PersianTextRenderer()

# Create test image
img = np.zeros((600, 1000, 3), dtype=np.uint8)

# Test texts (Persian)
tests = [
    ("سلام! خوش آمدید به نمایشگاه", 50, 30, (255, 255, 255)),
    ("آیینه هوشمند الکامپ اصفهان 🎥", 120, 35, (0, 255, 0)),
    ("مهمان #42", 200, 25, (255, 200, 0)),
    ("سن: 28 ساله", 260, 25, (255, 255, 255)),
    ("جنسیت: آقا", 310, 25, (255, 255, 255)),
    ("احساس: 😊 خوشحال", 360, 25, (0, 255, 255)),
    ("بازدید: 3 بار", 410, 25, (200, 200, 255)),
]

print("Rendering test texts...")

for text, y, font_size, color in tests:
    print(f"  - {text}")
    img = renderer.put_text(
        img, text, (50, y),
        font_size=font_size,
        color=color,
        bg_color=(30, 30, 30),
        padding=5
    )

# Test centered text
print("  - Centered text")
img = renderer.put_text_centered(
    img, "💬 این یک پیام تست است", 500,
    font_size=28,
    color=(255, 255, 255),
    bg_color=(50, 50, 50)
)

# Display
print("\n✅ Rendering complete!")
print("\nDisplaying test image...")
print("Press any key to close the window")

cv2.imshow('Persian Font Test - فونت فارسی', img)
cv2.waitKey(0)
cv2.destroyAllWindows()

print("\n" + "="*60)
print("Test Results:")
print("="*60)
print("✅ If you see Persian text correctly: Font rendering works!")
print("❌ If you see squares/question marks: Font issue detected")
print("\nTo fix font issues:")
print("1. Make sure arabic-reshaper and python-bidi are installed")
print("2. Check if Persian fonts are available on your system")
print("3. On Windows: Check C:\\Windows\\Fonts\\")
print("="*60)