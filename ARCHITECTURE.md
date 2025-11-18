# 🏗️ معماری سیستم Smart Mirror

## نمای کلی

```
┌─────────────────────────────────────────────────────────┐
│                      MAIN.PY                            │
│              (Application Controller)                   │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Face Detector │  │Face Analyzer │  │   Database   │
│  (MediaPipe) │  │  (DeepFace)  │  │   (SQLite)   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Session Mgr   │  │AI Generator  │  │UI Renderer   │
│              │  │  (OpenAI)    │  │  (OpenCV)    │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 🔄 جریان اصلی برنامه

### 1. راه‌اندازی (Initialization)

```python
# main.py
app = SmartMirror()
├── config.py          # بارگذاری تنظیمات
├── database.py        # ایجاد/اتصال دیتابیس
├── face_detector.py   # مقداردهی MediaPipe
├── face_analyzer.py   # بارگذاری مدل‌های DeepFace
├── ai_generator.py    # اتصال به OpenAI
├── session_manager.py # آماده‌سازی session tracker
└── ui_renderer.py     # آماده‌سازی UI
```

### 2. حلقه اصلی (Main Loop)

```python
while True:
    # خواندن فریم از دوربین
    frame = camera.read()
    
    # تشخیص چهره‌ها (سریع - هر فریم)
    faces = face_detector.detect_faces(frame)
    
    if faces:
        # انتخاب بزرگترین چهره
        main_face = faces[0]
        
        # بلور بقیه چهره‌ها
        for secondary_face in faces[1:]:
            apply_blur(secondary_face)
        
        # استخراج embedding (سریع)
        embedding = face_analyzer.extract_embedding(main_face)
        
        # جستجو در دیتابیس
        profile = database.find_profile(embedding)
        
        if profile:
            # بازدیدکننده قبلی
            session = session_manager.get_or_create(profile)
            
            # آیا زمان تحلیل است؟
            if session.should_analyze():
                # تحلیل کامل (کند - هر 2-3 ثانیه)
                analysis = face_analyzer.analyze(main_face)
                
                # ساخت context
                context = build_context(profile, analysis)
                
                # تولید پیام
                ai_message = ai_generator.generate(context)
                
                # ذخیره در دیتابیس
                database.add_record(profile, analysis, ai_message)
                
                # بروزرسانی session
                session.update(analysis, ai_message)
        else:
            # بازدیدکننده جدید
            analysis = face_analyzer.analyze(main_face)
            profile = database.create_profile(embedding, analysis)
            ai_message = ai_generator.generate(context)
            session = session_manager.create(profile)
        
        # رسم UI
        rendered = ui_renderer.render(frame, main_face, session, stats)
    
    # نمایش
    cv2.imshow('Smart Mirror', rendered)
```

### 3. پاکسازی (Cleanup)

```python
# پایان سیشن‌ها
session_manager.cleanup_expired()

# بستن منابع
camera.release()
face_detector.close()
cv2.destroyAllWindows()
```

---

## 📦 ماژول‌ها

### 1. **config.py**
- بارگذاری تنظیمات از `.env`
- مدیریت مسیرها
- مقادیر ثابت (رنگ‌ها، فونت‌ها، ترجمه‌ها)

### 2. **database.py**
- مدیریت SQLite
- جداول: profiles, records, messages_cache
- عملیات CRUD
- جستجوی embedding با cosine similarity

### 3. **face_detector.py**
- تشخیص سریع چهره با MediaPipe
- استخراج bounding box
- محاسبه مساحت (برای sorting)
- اعمال blur

### 4. **face_analyzer.py**
- تحلیل چهره با DeepFace
- استخراج: سن، جنسیت، احساس
- استخراج embedding (Facenet 128D)
- مدیریت خطا و fallback

### 5. **ai_message_generator.py**
- تولید پیام با OpenAI GPT-4o-mini
- سیستم template-based prompting
- Cache هوشمند
- Fallback messages

### 6. **session_manager.py**
- ردیابی حضور بازدیدکنندگان
- مدیریت timeout
- تعیین زمان تحلیل
- پاکسازی خودکار

### 7. **ui_renderer.py**
- رسم header و footer
- باکس اطلاعات چهره اصلی
- نمایش پیام AI با انیمیشن
- آمار و FPS

---

## 🔑 تصمیمات طراحی کلیدی

### چرا MediaPipe؟
- ✅ خیلی سریع (60+ FPS)
- ✅ سبک (بدون GPU)
- ✅ دقت خوب برای real-time
- ❌ فقط detection (نه analysis)

### چرا DeepFace؟
- ✅ یک API برای همه (سن، جنسیت، احساس)
- ✅ چندین مدل backend
- ✅ مستندات خوب
- ❌ کند برای real-time
- **راه‌حل**: فقط هر 2-3 ثانیه تحلیل

### چرا Facenet برای Embedding؟
- ✅ سبک (128D)
- ✅ سریع
- ✅ دقت بالا برای face matching
- ❌ جایگزین: ArcFace (دقیق‌تر اما کندتر)

### چرا SQLite؟
- ✅ بدون نیاز به server
- ✅ سریع برای read/write
- ✅ مناسب برای 1000s profiles
- ❌ محدودیت: concurrent writes
- **مناسب برای**: نمایشگاه (single instance)

### چرا OpenAI GPT-4o-mini؟
- ✅ خیلی ارزان ($0.15/1M tokens)
- ✅ سریع
- ✅ فارسی خوب
- ❌ نیاز به اینترنت
- **راه‌حل**: Fallback messages

---

## ⚡ بهینه‌سازی‌ها

### 1. Two-Tier Processing

```
Tier 1: هر فریم (سریع)
├── تشخیص چهره (MediaPipe)
├── Sorting بر اساس area
├── Blur کردن secondary faces
└── رسم bounding boxes

Tier 2: هر 2-3 ثانیه (کند)
├── استخراج embedding
├── جستجو در دیتابیس
├── تحلیل کامل (سن، جنسیت، احساس)
└── تولید پیام AI
```

### 2. Caching Strategy

```python
# Embedding Cache
profile = db.find_by_embedding(embedding)
# اگر یافت شد، نیازی به تحلیل مجدد نیست

# Message Cache
cached_msg = db.get_cached_message(context_hash)
# اگر context مشابه، از cache استفاده کن
```

### 3. Session Management

```python
# تشخیص حضور
if time_since_last_seen > 3s:
    end_session()
else:
    continue_session()

# زمان‌بندی تحلیل
if time_since_last_analysis > 2.5s:
    perform_analysis()
```

### 4. Resource Management

```python
# تنها موارد ضروری در RAM
- تصویر فعلی
- Embeddings فعال
- Session state

# در دیسک
- عکس‌ها
- تاریخچه کامل
- Message cache
```

---

## 🎯 نکات عملکرد

### معیارهای موفقیت:
- **FPS**: >20 (smooth)
- **تاخیر تشخیص**: <500ms
- **تاخیر تحلیل**: <3s
- **دقت matching**: >95%
- **استفاده RAM**: <3GB
- **استفاده CPU**: <70%

### بطری‌گردن‌ها (Bottlenecks):
1. **DeepFace.analyze()**: ~2s
2. **DeepFace.represent()**: ~1s
3. **OpenAI API call**: ~500ms
4. **Database search**: <10ms ✅

### راه‌حل‌ها:
- ✅ Tier 1/2 separation
- ✅ Analysis interval
- ✅ Caching
- ✅ Session management

---

## 🔮 قابلیت‌های آینده

### Phase 2:
- [ ] GPU acceleration
- [ ] Multiple camera support
- [ ] Dashboard مدیریتی
- [ ] Export statistics

### Phase 3:
- [ ] Cloud sync
- [ ] API برای integration
- [ ] Mobile app
- [ ] Advanced analytics

---

## 🐛 دیباگ

### لاگ سطوح:

```python
DEBUG = True  # در config.py

# خروجی:
🔍 Analyzing returning visitor (Profile 42)...
✅ Analysis complete | Message: سلام دوباره!
⏱️  Session ended (duration: 12s)
📊 Stats: 247 visitors, 42 today
```

### Profiling:

```bash
# زمان‌سنجی
python -m cProfile -o profile.stats main.py

# تحلیل
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumtime').print_stats(20)"
```

---

این معماری برای **قابلیت اطمینان، سرعت و مقیاس‌پذیری** طراحی شده است! 🚀