# YouTube Faceless Channel — Full Automation (Rs. 0/month)

Roz **3 videos + 3 shorts** (Urdu facts) khud ban kar upload hongi. Setup sirf **ek baar** karna hai (30–45 min), phir sab automatic.

---

## System kaise kaam karta hai

```
GitHub Actions (roz 9:30 AM PKT par chalta hai)
   │
   ├─ 1. Gemini API ........... topics + Urdu scripts likhta hai
   ├─ 2. edge-tts ............. Urdu voiceover banata hai (free, no key)
   ├─ 3. Pexels API ........... stock footage download karta hai
   ├─ 4. FFmpeg/MoviePy ....... final video render karta hai
   └─ 5. YouTube API .......... channel par upload karta hai
```

---

## STEP 1 — Gemini API key (free) — 2 min

1. https://aistudio.google.com/apikey kholein
2. Google account se login → **Create API key**
3. Key copy kar ke kahin save kar lein → yeh `GEMINI_API_KEY` hai

## STEP 2 — Pexels API key (free) — 2 min

1. https://www.pexels.com/api/ kholein → **Get Started** → account banayein
2. Dashboard se API key copy karein → yeh `PEXELS_API_KEY` hai

## STEP 3 — YouTube API setup — 15 min (sab se lamba step)

1. https://console.cloud.google.com kholein → naya **Project** banayein
2. **APIs & Services → Library** → "YouTube Data API v3" search kar ke **Enable** karein
3. **APIs & Services → OAuth consent screen**:
   - External → App ka koi bhi naam → apni email → Save
   - **Audience/Test users** mein apni email add karein
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Desktop app** → Create
   - **Download JSON** karein, file ka naam `client_secret.json` rakhein

5. Ab apne computer par (Python installed hona chahiye):
   ```
   pip install google-auth-oauthlib google-api-python-client
   ```
   `client_secret.json` ko is project folder mein rakhein, phir:
   ```
   python get_refresh_token.py
   ```
   Browser khulega → **apne YouTube channel wale account** se login → Allow.
   Terminal mein 3 values print hongi:
   - `YT_CLIENT_ID`
   - `YT_CLIENT_SECRET`
   - `YT_REFRESH_TOKEN`

   Teeno save kar lein.

## STEP 4 — GitHub par lagana — 10 min

1. https://github.com par account banayein (agar nahi hai)
2. **New repository** → naam e.g. `yt-automation` → **Private** rakh sakte hain
   - Note: Private repo par GitHub Actions ke 2,000 free minutes/month hain.
     Yeh pipeline roughly 40–60 min/din leta hai, to mahine ke ~1,500–1,800 min —
     limit ke andar, lekin agar kabhi kam parein to repo **Public** kar dein
     (public repos par minutes unlimited free hain).
3. Is poore folder ki files repo mein upload karein
   (GitHub par "uploading an existing file" se drag & drop bhi ho jata hai —
   `.github/workflows/daily.yml` ka folder path same rehna zaroori hai)
4. Repo mein: **Settings → Secrets and variables → Actions → New repository secret**
   Yeh **5 secrets** banayein:

   | Secret name        | Value                  |
   |--------------------|------------------------|
   | `GEMINI_API_KEY`   | Step 1 wali key        |
   | `PEXELS_API_KEY`   | Step 2 wali key        |
   | `YT_CLIENT_ID`     | Step 3 wali value      |
   | `YT_CLIENT_SECRET` | Step 3 wali value      |
   | `YT_REFRESH_TOKEN` | Step 3 wali value      |

## STEP 5 — Pehla test run

1. Repo mein **Actions** tab → "Daily YouTube Videos" → **Run workflow**
2. Logs mein progress dekhein. 40–60 min mein 6 videos upload ho jani chahiye.
3. Pehli dafa `config.py` mein `PRIVACY_STATUS = "private"` rakh kar test karein,
   videos check karein, phir `"public"` kar dein.

Bas. Ab roz 9:30 AM par sab khud hoga. ✅

---

## Customize karna (sirf `config.py` edit karein)

| Setting | Kya karti hai |
|---|---|
| `VOICE` | `ur-PK-UzmaNeural` = female Urdu, `hi-IN-SwaraNeural` = Hindi |
| `NICHE` | Topics ka subject change karein |
| `LONG_VIDEOS_PER_DAY` / `SHORTS_PER_DAY` | Videos ki tadaad |
| `PRIVACY_STATUS` | `private` / `public` |
| Upload time | `.github/workflows/daily.yml` mein cron (UTC mein hota hai; PKT − 5) |

## Important baatein (zaroor parhein)

- **YouTube quota:** Free quota 10,000 units/din hai; har upload ~1,600 units leta hai.
  6 uploads = 9,600 units — bilkul limit par. Isi liye 6 se zyada na karein.
- **Monetization warning:** YouTube "mass-produced / repetitious" content ko
  monetization se reject kar sakta hai. Bachne ke liye: thumbnails custom banayein,
  kabhi kabhi scripts edit karein, aur quality par nazar rakhein. Yeh system content
  banata hai — channel ki growth strategy phir bhi aap ki hai.
- **Gemini free tier limits:** Agar kabhi rate limit aaye to script khud 30 sec
  wait kar ke retry karta hai.
- **Token expire:** Agar mahino baad upload fail ho "invalid_grant" ke saath,
  to Step 3.5 dobara chala kar naya refresh token banayein.
  (OAuth consent screen ko "Testing" se "In production" karne par token
  expire nahi hota — warna testing mode mein 7 din baad expire ho jata hai.
  Is liye consent screen ko **Publish/In production** zaroor kar dein.)

## Troubleshooting

| Masla | Hal |
|---|---|
| Action fail "Gemini API failed" | Key check karein, ya free tier limit — agle din theek |
| "Footage nahi mili" | Pexels key check karein |
| Upload fail 403 | YouTube API enable hai? Consent screen published hai? |
| Video Urdu nahi bol rahi | `config.py` mein `VOICE` check karein |
