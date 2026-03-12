# 🎬 CogniWatch Avatar Setup Guide
# Talking AI Security Analyst

CogWatch can now **talk to you** via a photorealistic AI avatar powered by D-ID!

---

## 🚀 Quick Setup

### 1. Get D-ID API Key

1. Sign up at https://www.d-id.com/
2. Go to **Account Settings** → **API Keys**
3. Create new API key
4. **Free tier:** 20 credits/month (enough for ~20 videos)

### 2. Add to Environment

Edit `/home/cogniwatch/.env`:

```bash
# D-ID Avatar API
DID_API_KEY=your_api_key_here
```

### 3. Restart Containers

```bash
cd /home/cogniwatch
docker compose restart cogniwatch-webui
```

### 4. Test It!

```bash
curl http://localhost:9000/api/avatar/test
```

Should return:
```json
{"status": "ok", "message": "Avatar API is ready", "configured": true}
```

---

## 💬 How It Works

**When a scan completes:**

1. CogniWatch generates summary text
   > "Scan complete! Found 3 AI agents: OpenClaw on port 18789, CrewAI on 192.168.0.45..."

2. Backend calls D-ID API with text + avatar image

3. D-ID generates talking head video (~30 seconds render)

4. Video plays automatically in dashboard (bottom-right corner)

5. You hear + see the analysis!

---

## 🎨 Avatar Options

### Default Avatar
Uses D-ID's default presenter (Alan)

### Custom Avatar
Generate your own avatar image (DALL-E, Midjourney, etc.) then:

```bash
# Upload to D-ID or host publicly
# Add to .env:
DID_AVATAR_IMAGE_URL=https://your-server.com/neo-avatar.png
```

---

## 💰 Pricing & Credits

**D-ID Free Tier:**
- 20 credits/month
- ~1 credit per 10 seconds of video
- **~200 seconds/month** (plenty for demo!)

**Paid Plans:**
- $5.99/mo: 1200 credits (~200 min)
- Custom: Enterprise volumes

**For CogniWatch:**
- Scan summaries: ~15-30 seconds each
- Alert notifications: ~10 seconds each
- Q&A responses: ~10-20 seconds each

**Free tier is enough for testing + light usage!**

---

## 🔧 Manual Usage

```python
from webui.avatar_integration import generate_avatar_response

# Generate video
video_path = generate_avatar_response(
    "Hi! I'm your CogniWatch AI analyst. Your network is secure with 2 agents detected."
)

# Returns: /home/cogniwatch/webui/static/avatars/avatar-abc123.mp4
```

---

## 🎯 Use Cases

1. **Scan Results** - Avatar explains findings after each scan
2. **Alert Notifications** - Voice warnings for high-risk agents
3. **Onboarding** - Welcome video for new users
4. **Help System** - Avatar guides users through features
5. **Demo Mode** - Auto-play when visitors land on dashboard

---

## 🚨 Troubleshooting

**D-ID API key error:**
```bash
echo $DID_API_KEY  # Check it's set
docker compose logs cogniwatch-webui  # Check logs
```

**Video not playing:**
- Check browser supports MP4/H.264
- Click video manually (autoplay may be blocked)
- Check file was downloaded: `ls /home/cogniwatch/webui/static/avatars/`

**Slow rendering:**
- D-ID takes ~30-60 seconds to generate
- Free tier may be slower during peak times
- Consider caching common responses

---

## 🎬 Next Steps (Phase 2)

- [ ] Always-on idle animation (breathing avatar)
- [ ] Click-to-ask questions ("What's high-risk?")
- [ ] Voice input (click mic, speak questions)
- [ ] Multiple avatar personas (choose your analyst)
- [ ] Emotion detection (serious for alerts, friendly for demos)

---

**Questions?** Check `/home/cogniwatch/webui/avatar_integration.py` for the code!
