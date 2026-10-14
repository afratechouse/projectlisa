# Project "Lisa" – Cloud Deployment & Multi-Device Setup Guide

এই গাইডের মাধ্যমে আপনার লোকাল প্রজেক্টটিকে একটি ক্লাউড সার্ভারে (যেমন **Render** বা **Railway**) লাইভ করা হবে, যাতে একটিমাত্র সেন্ট্রাল এআই মডেল দিয়ে আপনি মোবাইল এবং ল্যাপটপ উভয় জায়গা থেকেই হোয়াটসঅ্যাপের মাধ্যমে লিসাকে ২৪/৭ ব্যবহার করতে পারেন।

---

## 🛠️ Step 1: প্রজেক্টে Procfile ও এন্ট্রি পয়েন্ট তৈরি (সম্পন্ন ✅)
ক্লাউড সার্ভারকে জানানোর জন্য যে কোন কমান্ডে সার্ভার চালু হবে:
- প্রজেক্ট রুটে **[Procfile](file:///e:/asistant-lisa/Procfile)** তৈরি করা হয়েছে:
  ```text
  web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
- রুটে **[main.py](file:///e:/asistant-lisa/main.py)** অ্যালিয়াস ফাইলও যুক্ত করা হয়েছে, যাতে `main:app` বা `app.main:app` যেভাবেই রান করা হোক সার্ভার ক্র্যাশ না করে।
- **[.gitignore](file:///e:/asistant-lisa/.gitignore)** তৈরি করা হয়েছে যাতে আপনার `.env` ও সিক্রেট API কী গিটহাবে লিক না হয়।
- রেন্ডারের জন্য অটোমেটিক ব্লুপ্রিন্ট **[render.yaml](file:///e:/asistant-lisa/render.yaml)** তৈরি করা হয়েছে।

---

## 🚀 Step 2: GitHub-এ কোড আপলোড করা
আমরা ইতিমধ্যেই লোকাল গিট ইনিশিয়ালাইজ ও ইনিশিয়াল কমিট সম্পন্ন করে রেখেছি। এখন শুধু আপনার গিটহাব অ্যাকাউন্টে পুশ করতে হবে:

1. **[GitHub.com](https://github.com)** এ যান এবং একটি নতুন রিপোজিটরি তৈরি করুন (যেমন: `project-lisa`)।
2. আপনার টার্মিনালে নিচের কমান্ডগুলো রান করুন (আপনার রিপোজিটরির লিংক দিয়ে):
   ```bash
   git branch -M main
   git remote add origin https://github.com/<your-username>/project-lisa.git
   git push -u origin main
   ```

---

## ☁️ Step 3: Cloud Hosting-এ ডিপ্লয় করা (Render.com)

1. **[Render.com](https://render.com)** এ ফ্রি একাউন্ট খুলুন (Sign in with GitHub)।
2. ড্যাশবোর্ডে **New +** এ ক্লিক করে **Web Service** সিলেক্ট করুন।
3. আপনার গিটহাব রিপোজিটরি (`project-lisa`) কানেক্ট করুন।
4. সেটিংস নিচের মতো কনফিগার করুন:
   - **Name:** `lisa-backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free`

5. **Environment Variables** সেকশনে নিচের কীগুলো যোগ করুন:
   ```text
   APP_ENV = production
   GEMINI_API_KEY = আপনার Google AI Studio এপিআই কী
   GEMINI_MODEL = gemini-2.5-pro
   AUTHORIZED_PHONE_NUMBER = আপনার হোয়াটসঅ্যাপ নম্বর (যেমন: 88017XXXXXXXX)
   MASTER_PIN_HASH = আপনার 4-ডিজিট পিন হ্যাশ
   EVOLUTION_API_BASE_URL = আপনার Evolution API সার্ভারের URL
   EVOLUTION_API_KEY = lisa_secret_evolution_key
   DEEPGRAM_API_KEY = আপনার Deepgram এপিআই কী
   ELEVENLABS_API_KEY = আপনার ElevenLabs এপিআই কী
   ELEVENLABS_VOICE_ID = 21m00Tcm4TlvDq8ikWAM
   ```

> [!TIP]
> **ক্লাউড ডেটাবেজ (100% ফ্রি):**
> - **Redis:** [Upstash.com](https://upstash.com)-এ ফ্রি Redis তৈরি করে হোস্ট, পোর্ট ও পাসওয়ার্ড দিন।
> - **Qdrant:** [cloud.qdrant.io](https://cloud.qdrant.io)-এ ফ্রি ক্লাস্টার তৈরি করে Qdrant হোস্ট ও এপিআই কী দিন।

ডিপ্লয় সফল হলে রেন্ডার আপনাকে একটি লাইভ সিকিউর URL দেবে (যেমন: `https://lisa-backend.onrender.com`)।

---

## 📲 Step 4: WhatsApp Gateway (Evolution API) কানেকশন

1. আপনার Evolution API ড্যাশবোর্ড বা ইনস্ট্যান্সের ওয়েবহুক সেটিংসে প্রবেশ করুন।
2. **Webhook URL** হিসেবে রেন্ডারের লাইভ লিংকটি সেট করুন:
   ```text
   https://lisa-backend.onrender.com/webhook/evolution
   ```
3. ইভেন্ট হিসেবে `MESSAGES_UPSERT` এনেবল করে সেভ করুন।
4. Evolution API-এর QR কোড স্ক্যান করে লিসার হোয়াটসঅ্যাপ নম্বরটি কানেক্ট করুন।

---

## 💻📱 Step 5: ল্যাপটপ ও মোবাইলে একসাথে ব্যবহার

লিসা ক্লাউডে রান করায় আপনার নিজের কম্পিউটার বন্ধ থাকলেও লিসা ২৪/৭ সক্রিয় থাকবে:

1. **মোবাইলে ব্যবহার:**
   - আপনার ফোনের অফিশিয়াল WhatsApp অ্যাপ থেকে লিসার নম্বরে সরাসরি টেক্সট বা ভয়েস নোট পাঠিয়ে কথা বলুন ও কাজ করান।
2. **ল্যাপটপে ব্যবহার:**
   - ব্রাউজারে **web.whatsapp.com** ওপেন করে বা ল্যাপটপের WhatsApp Desktop অ্যাপ থেকে চ্যাট করুন।
   - এছাড়াও ল্যাপটপের ব্রাউজারে সরাসরি লিসার লাইভ ভিজ্যুয়াল ইন্টারফেস ব্যবহার করতে পারেন:
     ```text
     https://lisa-backend.onrender.com/avatar
     ```
     যেখানে লিসার অফিশিয়াল ভিজ্যুয়াল মডেল লাইভ স্ক্রিনে কথা বলবে ও কমান্ড গ্রহণ করবে!