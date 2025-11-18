# 🚀 راهنمای سریع شروع

## نصب سریع (5 دقیقه)

### 1. دانلود و آماده‌سازی

```bash
# باز کردن ترمینال در پوشه پروژه
cd smart-mirror-elecomp
```

### 2. نصب Python Packages

```bash
pip install opencv-python mediapipe deepface openai python-dotenv scikit-learn
```

### 3. ایجاد فایل .env

```bash
# کپی کردن نمونه
cp .env.example .env

# ویرایش با ویرایشگر دلخواه
notepad .env      # Windows
nano .env         # Linux/Mac
```

**محتوای .env:**
```
OPENAI_API_KEY=sk-your-key-here
CAMERA_INDEX=0
```

### 4. اجرا!

```bash
python main.py
```

---

## ⚡ تست سریع اجزا

### تست دوربین:
```bash
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera FAILED')"
```

### تست MediaPipe:
```bash
python src/face_detector.py
```

### تست DeepFace:
```bash
python src/face_analyzer.py
```

### تست پایگاه داده:
```bash
python src/database.py
```

---

## 🎯 مراحل اولین اجرا

1. **راه‌اندازی اول (2-3 دقیقه):**
   - مدل‌ها دانلود می‌شوند
   - پایگاه داده ایجاد می‌شود
   - صبر کنید تا "Smart Mirror initialized" نمایش داده شود

2. **تست:**
   - جلوی دوربین بایستید
   - باید باکس سبز دور چهره‌تان ظاهر شود
   - بعد از 2-3 ثانیه تحلیل انجام می‌شود
   - پیام AI نمایش داده می‌شود

3. **تست بازدید مجدد:**
   - از جلوی دوربین دور شوید (3 ثانیه)
   - دوباره برگردید
   - باید پیام متفاوتی دریافت کنید!

---

## ❓ مشکلات رایج

### خطا: "Failed to open camera"
```bash
# تست دوربین‌های مختلف:
CAMERA_INDEX=1 python main.py
CAMERA_INDEX=2 python main.py
```

### خطا: "OpenAI API key not found"
```bash
# بررسی کنید .env وجود دارد
ls -la .env

# محتوا را چک کنید
cat .env | grep OPENAI_API_KEY
```

### سرعت کند
```bash
# کیفیت پایین‌تر = سرعت بیشتر
# در .env:
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
ANALYSIS_INTERVAL=3.5
```

---

## 📊 تست موفقیت‌آمیز

اگر این‌ها را می‌بینید، همه چیز کار می‌کند:

```
✅ Configuration loaded successfully
✅ Database initialized
✅ Face detector initialized (MediaPipe)
✅ Face analyzer initialized (DeepFace)
✅ AI message generator initialized (OpenAI)
✅ Session manager initialized
✅ UI renderer initialized
✅ Camera initialized
✅ Smart Mirror initialized successfully!

🚀 Starting Smart Mirror...
```

---

## 🎮 دستورات مفید

```bash
# مشاهده آمار در حین اجرا
# فشار دادن کلید 's' در پنجره برنامه

# مشاهده دیتابیس
sqlite3 data/database.db "SELECT COUNT(*) FROM profiles;"

# پاک کردن همه داده‌ها (شروع از نو)
rm data/database.db
rm -rf data/photos/*

# نمایش لاگ‌های دقیق
DEBUG=True python main.py
```

---

## 💡 نکات

1. **اولین بار**: دانلود مدل‌ها طول می‌کشد، صبور باشید
2. **نور مناسب**: نور خوب = تشخیص بهتر
3. **فاصله**: 50-100 سانتی‌متر از دوربین
4. **صبر**: تحلیل 2-3 ثانیه طول می‌کشد

---

## 🔥 آماده نمایشگاه

```bash
# 1. تست کامل
python main.py

# 2. بررسی عملکرد
# - FPS باید >20 باشد
# - تحلیل باید <3 ثانیه باشد
# - پیام‌ها باید نمایش داده شوند

# 3. آماده!
```

موفق باشید! 🎉