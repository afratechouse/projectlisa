Project "Lisa" - Cloud Deployment & Multi-Device Setup Guide
এই গাইডের মাধ্যমে আপনার লোকাল প্রজেক্টটিকে একটি ক্লাউড সার্ভারে (যেমন Render বা Railway) লাইভ করা হবে, যাতে একটিমাত্র সেন্ট্রাল এআই মডেল দিয়ে আপনি মোবাইল এবং ল্যাপটপ উভয় জায়গা থেকেই হোয়াটসঅ্যাপের মাধ্যমে লিসাকে ব্যবহার করতে পারেন।

Step 1: প্রজেক্টে Procfile তৈরি করা
ক্লাউড সার্ভারকে জানানোর জন্য যে কোন কমান্ডে সার্ভার চালু হবে, প্রজেক্ট ফোল্ডারে Procfile নামে একটি ফাইল তৈরি করুন (কোনো এক্সটেনশন হবে না) এবং নিচের লাইনটি লিখে সেভ করুন:

Plaintext
web: uvicorn main:app --host 0.0.0.0 --port $PORT
Step 2: GitHub-এ কোড আপলোড করা
আপনার প্রজেক্ট ফোল্ডারটি GitHub-এ একটি নতুন রিপোজিটরিতে (যেমন project-lisa) পুশ বা আপলোড করুন। নিশ্চিত করুন যে আপনার নিচের ফাইলগুলো গিটহাবে আছে:

main.py

requirements.txt

Procfile

docker-compose.yml (যদি ডাটাবেজ লোকালি বা ক্লাউডে রান করতে চান)

Step 3: Cloud Hosting-এ ডিপ্লয় করা (Render / Railway)
Render.com (অথবা Railway.app)-এ আপনার জিমেইল দিয়ে ফ্রি একাউন্ট খুলুন।

New + এ ক্লিক করে Web Service সিলেক্ট করুন।

আপনার গিটহাব রিপোজিটরি (project-lisa) কানেক্ট করুন।

সেটিংস নিচের মতো দিন:

Build Command: pip install -r requirements.txt

Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT

Environment Variables সেকশনে নিচের কিগুলো যুক্ত করুন:

GEMINI_API_KEY = আপনার গুগল এআই স্টুডিও এপিআই কি

AUTHORIZED_PHONE_NUMBER = আপনার হোয়াটসঅ্যাপ নম্বর (যেমন: 88017xxxxxxxx)

ডিপ্লয় সফল হলে রেন্ডার আপনাকে একটি লাইভ URL দিবে (যেমন: [https://lisa-backend.onrender.com](https://lisa-backend.onrender.com))।

Step 4: WhatsApp Gateway (Evolution API) কানেকশন
আপনার Evolution API সার্ভার বা ডকার কন্টেইনারে ক্লাউড সার্ভার লিংকটি ওয়েবহাউক (Webhook) হিসেবে সেট করুন:

Webhook URL: [https://lisa-backend.onrender.com/webhook/evolution](https://lisa-backend.onrender.com/webhook/evolution)

Evolution API-এর QR কোড স্ক্যান করে আপনার হোয়াটসঅ্যাপ নম্বরটি কানেক্ট করুন।

Step 5: ল্যাপটপ ও মোবাইলে একসাথে ব্যবহার
একবার ক্লাউড ডিপ্লয়মেন্ট ও হোয়াটসঅ্যাপ কানেকশন কমপ্লিট হয়ে গেলে:

মোবাইলে: আপনার ফোনের অফিশিয়াল WhatsApp অ্যাপ থেকে লিসার চ্যাটবটে টেক্সট বা ভয়েস নোট পাঠাতে পারবেন।

ল্যাপটপে: ব্রাউজারে web.whatsapp.com ওপেন করে বা ল্যাপটপের WhatsApp অ্যাপ থেকে একই নম্বরে চ্যাট করতে পারবেন।