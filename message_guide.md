# AI Message Configuration Guide 🤖

## Quick Setup

### Option 1: Use Static Messages (No API cost) 💰

Edit `config.yaml`:
```yaml
ai_message:
  enabled: false  # ← Set to false
  
  static_messages:
    welcome: "به نمایشگاه الکامپ خوش آمدید! 🎉"
    returning: "خوشحالیم دوباره میبینیمتون! ✨"
    default: "به آینه هوشمند الکامپ اصفهان خوش آمدید! 🎥"
```

**Result:**
- ✅ No OpenAI API needed
- ✅ No internet required
- ✅ Zero cost
- ✅ Instant messages
- ❌ Same message for everyone

---

### Option 2: Use AI/LLM (Dynamic messages) 🧠

Edit `config.yaml`:
```yaml
ai_message:
  enabled: true  # ← Set to true
  use_cache: true  # Recommended to save API calls
```

Don't forget `.env`:
```
OPENAI_API_KEY=sk-your-key-here
```

**Result:**
- ✅ Personalized messages
- ✅ Different for each person
- ✅ Creative & engaging
- ❌ Requires API key
- ❌ Small cost (~$0.00005 per message)

---

## Configuration Details

### Static Message Types

```yaml
static_messages:
  welcome: "..."    # First-time visitors
  returning: "..."  # Visitors who return today
  default: "..."    # Fallback for any case
```

**You can use:**
- Persian text: `به نمایشگاه خوش آمدید`
- Emojis: `🎉 ✨ 🎥 💫 🌟`
- Multi-line (use `|`):
  ```yaml
  welcome: |
    به نمایشگاه الکامپ خوش آمدید!
    امیدواریم تجربه خوبی داشته باشید 🎉
  ```

---

## Examples

### Example 1: Exhibition Welcome (Simple)
```yaml
ai_message:
  enabled: false
  
  static_messages:
    welcome: "به نمایشگاه الکامپ خوش آمدید! 🎉"
    returning: "خوشحالیم دوباره میبینیمتون! 🌟"
    default: "سلام! 👋"
```

### Example 2: Exhibition Welcome (Detailed)
```yaml
ai_message:
  enabled: false
  
  static_messages:
    welcome: "🎉 به نمایشگاه الکامپ اصفهان خوش آمدید! امیدواریم تجربه فوق‌العاده‌ای داشته باشید!"
    returning: "✨ چه خوب که دوباره اومدید! از دیدن شما خوشحالیم!"
    default: "👋 به آینه هوشمند الکامپ خوش آمدید!"
```

### Example 3: Tech Event
```yaml
ai_message:
  enabled: false
  
  static_messages:
    welcome: "🚀 Welcome to EleComp Isfahan! Explore the future of technology!"
    returning: "💫 Great to see you again! Discover more innovation!"
    default: "🎯 Smart Mirror by EleComp Isfahan"
```

### Example 4: Mixed (AI with fallback)
```yaml
ai_message:
  enabled: true  # Uses AI when available
  use_cache: true
  
  static_messages:  # Used as fallback if API fails
    default: "به نمایشگاه الکامپ خوش آمدید! 🎉"
```

---

## How It Works

### When `enabled: false`:
```
New visitor → "welcome" message
Return today → "returning" message
Other cases → "default" message
```

### When `enabled: true`:
```
New visitor → AI generates creative message
Return today → AI with Hafez poem
API fails → Uses static_messages['default']
```

---

## Testing

### Test Static Messages:
```bash
# 1. Edit config.yaml
ai_message:
  enabled: false

# 2. Run
python main.py

# 3. Face the camera
# You should see your static message!
```

### Test AI Messages:
```bash
# 1. Edit config.yaml
ai_message:
  enabled: true

# 2. Add API key to .env
OPENAI_API_KEY=sk-...

# 3. Run
python main.py

# 4. Face the camera
# You should see unique AI-generated message!
```

---

## Cost Comparison

| Mode | Cost per visitor | 1000 visitors |
|------|-----------------|---------------|
| Static | $0 | $0 |
| AI (no cache) | $0.00005 | $0.05 |
| AI (with cache) | $0.00002 | $0.02 |

**Recommendation:** Use static messages for exhibitions/demos to avoid any costs.

---

## Troubleshooting

### Static messages not showing?
```yaml
# Make sure enabled is false (not true)
ai_message:
  enabled: false  # ← Check this
```

### AI not working?
```bash
# Check API key
cat .env | grep OPENAI_API_KEY

# Should show:
# OPENAI_API_KEY=sk-...

# If empty, add your key
```

### Persian text broken?
- Make sure `config.yaml` is saved as UTF-8
- Test with simple text first: `سلام`

---

## Quick Switch

To quickly switch between modes, just change one line:

```yaml
# For exhibition (no cost):
ai_message:
  enabled: false

# For testing AI:
ai_message:
  enabled: true
```

No need to restart! Changes take effect on next visitor.

---

**Recommendation for EleComp Exhibition:**
```yaml
ai_message:
  enabled: false  # Safe, zero cost, always works
  
  static_messages:
    welcome: "به نمایشگاه الکامپ اصفهان خوش آمدید! 🎉"
    returning: "خوشحالیم دوباره میبینیمتون! ✨"
    default: "به آینه هوشمند الکامپ خوش آمدید! 🎥"
```

Perfect for exhibitions! 🎯