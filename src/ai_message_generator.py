# File: src/ai_message_generator.py
"""
AI message generator using OpenAI API
Creative daily messages with Hafez poetry OR static messages
"""
import hashlib
import json
from typing import Dict, Optional
from datetime import datetime, timedelta
from openai import OpenAI
from src.config import (
    OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS,
    EMOTION_TRANSLATIONS, PROMPTS, HAFEZ_POEMS,
    AI_MESSAGE_ENABLED, AI_MESSAGE_USE_CACHE, STATIC_MESSAGES
)
from src.database import db


class AIMessageGenerator:
    """Generate personalized creative messages using OpenAI GPT or static messages"""
    
    def __init__(self):
        self.llm_enabled = AI_MESSAGE_ENABLED
        self.use_cache = AI_MESSAGE_USE_CACHE
        self.static_messages = STATIC_MESSAGES
        
        # Initialize OpenAI client only if LLM is enabled
        if self.llm_enabled:
            self.api_key = OPENAI_API_KEY
            self.model = OPENAI_MODEL
            
            if self.api_key:
                self.client = OpenAI(api_key=self.api_key)
                print("✅ AI message generator initialized (OpenAI LLM)")
            else:
                print("⚠️  OpenAI API key not found - using fallback messages")
                self.client = None
        else:
            self.client = None
            print("✅ AI message generator initialized (Static messages)")
            print(f"   Default message: {self.static_messages['default']}")
    
    def generate_message(self, context: Dict, use_cache: bool = None) -> str:
        """
        Generate personalized message based on context
        
        Args:
            context: Context dictionary with visitor info
            use_cache: Override default cache setting
        
        Returns:
            Generated or static message
        """
        # Use provided cache setting or default
        if use_cache is None:
            use_cache = self.use_cache and self.llm_enabled
        
        # If LLM is disabled, return static message
        if not self.llm_enabled:
            return self._get_static_message(context)
        
        # Check if same person visited today
        is_today_visit = self._is_today_visit(context)
        
        # Check cache only for today's messages
        if use_cache and is_today_visit:
            context_hash = self._create_hash(context)
            cached = db.get_cached_message(context_hash)
            if cached:
                return cached
        
        # Generate new message with LLM
        if self.client:
            message = self._generate_with_openai(context)
        else:
            message = self._generate_fallback(context)
        
        # Cache the message for today
        if use_cache and 'profile_id' in context:
            context_hash = self._create_hash(context)
            db.cache_message(context['profile_id'], context_hash, message)
        
        return message
    
    def _get_static_message(self, context: Dict) -> str:
        """
        Get static message based on context
        
        Args:
            context: Context dictionary
        
        Returns:
            Static message string
        """
        history = context.get('history', {})
        is_new = history.get('is_new', True)
        is_today_visit = self._is_today_visit(context)
        
        # First visit
        if is_new:
            return self.static_messages.get('welcome', self.static_messages['default'])
        
        # Return visit today
        elif is_today_visit:
            return self.static_messages.get('returning', self.static_messages['default'])
        
        # Default
        else:
            return self.static_messages.get('default', "به آینه هوشمند الکامپ خوش آمدید! 🎥")
    
    def _is_today_visit(self, context: Dict) -> bool:
        """Check if this is a return visit today"""
        history = context.get('history', {})
        
        if history.get('is_new', True):
            return False
        
        # Check if last visit was today
        last_seen = history.get('last_seen')
        if last_seen:
            try:
                if isinstance(last_seen, str):
                    last_seen = datetime.fromisoformat(last_seen)
                return last_seen.date() == datetime.now().date()
            except:
                pass
        
        return False
    
    def _generate_with_openai(self, context: Dict) -> str:
        """Generate message using OpenAI API"""
        prompt = self._build_prompt(context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": PROMPTS['system']
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=OPENAI_MAX_TOKENS,
                temperature=OPENAI_TEMPERATURE,
                top_p=0.95
            )
            
            message = response.choices[0].message.content.strip()
            return message
            
        except Exception as e:
            print(f"⚠️  OpenAI API error: {e}")
            return self._generate_fallback(context)
    
    def _build_prompt(self, context: Dict) -> str:
        """Build creative prompt based on context"""
        current = context.get('current', {})
        history = context.get('history', {})
        
        age = current.get('age', 25)
        gender = current.get('gender', 'Man')
        emotion = current.get('emotion', 'neutral')
        is_new = history.get('is_new', True)
        is_today_visit = self._is_today_visit(context)
        
        gender_fa = "خانم" if gender == "Woman" else "آقا"
        emotion_fa = EMOTION_TRANSLATIONS.get(emotion, emotion)
        
        # بازدید امروز - باید شعر حافظ داشته باشد
        if is_today_visit and not is_new:
            return PROMPTS['return_today'].format(
                gender=gender_fa,
                age=age,
                emotion=emotion_fa
            )
        
        # بازدید اول
        if is_new:
            if emotion in ['happy', 'surprise']:
                return f"""یک پیام خلاقانه و الهام‌بخش برای یک {gender_fa} {age} ساله که {emotion_fa} است.

پیام باید:
- خلاقانه و متفاوت
- به انرژی مثبت او اشاره کند
- الهام‌بخش باشد
- حداکثر 2 جمله
- یک ایموجی
- هیچ اشاره‌ای به "اولین بار" نباشد

مثال:
"انرژی تو فضا رو روشن می‌کنه! امروز روز خوبیه ✨"
"""
            
            elif emotion in ['sad', 'angry', 'fear']:
                return f"""یک پیام دلگرم‌کننده برای یک {gender_fa} {age} ساله که {emotion_fa} است.

پیام باید:
- محترمانه و همدلانه
- الهام‌بخش و امیدوارکننده
- شاعرانه و زیبا
- هیچ اشاره‌ای به "اولین بار" نباشد

مثال:
"بعد از هر شب، سحر است! امیدوارم لحظات خوب نزدیکه 🌅"
"""
            
            else:
                return f"""یک پیام خلاقانه برای یک {gender_fa} {age} ساله.

پیام باید الهام‌بخش و مثبت باشد.

مثال:
"هر لحظه یک فرصت جدید است! امروز چی می‌سازی? 🎯"
"""
        
        # بازدیدهای بعدی (نه امروز)
        else:
            if emotion in ['happy', 'surprise']:
                return f"""یک پیام خلاقانه برای یک {gender_fa} که {emotion_fa} است.

پیام باید الهام‌بخش و شاد باشد. هیچ اشاره‌ای به دفعات بازدید نباشد.

مثال:
"این انرژی مثبت رو نگه دار! روزهای خوب در راهه 🌈"
"""
            
            elif emotion in ['sad', 'angry']:
                return f"""یک پیام دلگرم‌کننده برای یک {gender_fa} که {emotion_fa} است.

پیام باید همدلانه و امیدوارکننده باشد.

مثال:
"طوفان‌ها گذرا هستند، قدرت تو همیشگی! 💪"
"""
            
            else:
                return f"""یک پیام خلاقانه برای یک {gender_fa}.

پیام باید منحصر به فرد و الهام‌بخش باشد.

مثال:
"هر لحظه پر از امکانات جدیده! امروز چی می‌خوای بسازی? 🎨"
"""
    
    def _generate_fallback(self, context: Dict) -> str:
        """Generate fallback message when API unavailable"""
        current = context.get('current', {})
        emotion = current.get('emotion', 'neutral')
        is_today_visit = self._is_today_visit(context)
        is_new = context.get('history', {}).get('is_new', True)
        
        # پیام حافظ برای بازدید مجدد امروز
        if is_today_visit and not is_new:
            import random
            return random.choice(HAFEZ_POEMS)
        
        # پیام‌های خلاقانه عادی
        if emotion in ['happy', 'surprise']:
            messages = [
                "انرژی تو فضا رو روشن می‌کنه! امروز روز خوبیه 🌟",
                "این لبخند رو نگه دار! چیزهای خوب در راهه ✨",
                "خوشحالی تو واگیر داره! امروز روز شگفتی‌هاست 🎯",
            ]
        elif emotion in ['sad', 'angry', 'fear']:
            messages = [
                "بعد از هر شب، سحر است! امیدوارم لحظات خوب نزدیکه 🌅",
                "طوفان‌ها گذرا هستند، قدرت تو همیشگی! 💪",
                "این هم می‌گذرد... چیزهای خوب در راهه 🌸",
            ]
        else:
            messages = [
                "هر لحظه پر از امکانات جدیده! امروز چی می‌سازی? 🎨",
                "انرژی امروز فوق‌العادست! یه چیز جدید امتحان کن 🚀",
                "این لحظه شروع یک ماجرای جدیده! آماده‌ای? ⚡",
            ]
        
        import random
        return random.choice(messages)
    
    def _create_hash(self, context: Dict) -> str:
        """Create hash for context caching"""
        today = datetime.now().date().isoformat()
        key_data = {
            'date': today,
            'emotion': context.get('current', {}).get('emotion', 'neutral'),
            'is_today_return': self._is_today_visit(context)
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()


# Test
if __name__ == "__main__":
    generator = AIMessageGenerator()
    
    print("\n" + "="*60)
    print("Testing AI Message Generator")
    print("="*60)
    print(f"LLM Enabled: {generator.llm_enabled}")
    print(f"Use Cache: {generator.use_cache}")
    print("="*60)
    
    scenarios = [
        {
            'name': 'First visit - happy',
            'context': {
                'current': {'age': 28, 'gender': 'Woman', 'emotion': 'happy'},
                'history': {'is_new': True, 'visit_number': 1}
            }
        },
        {
            'name': 'Return today - needs Hafez poem',
            'context': {
                'current': {'age': 28, 'gender': 'Woman', 'emotion': 'happy'},
                'history': {
                    'is_new': False,
                    'visit_number': 2,
                    'last_seen': datetime.now().isoformat()
                },
                'profile_id': 1
            }
        },
        {
            'name': 'Return another day',
            'context': {
                'current': {'age': 30, 'gender': 'Man', 'emotion': 'neutral'},
                'history': {
                    'is_new': False,
                    'visit_number': 3,
                    'last_seen': (datetime.now() - timedelta(days=1)).isoformat()
                },
                'profile_id': 2
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{'='*50}")
        print(f"Scenario: {scenario['name']}")
        print(f"{'='*50}")
        message = generator.generate_message(scenario['context'], use_cache=False)
        print(f"Message: {message}")