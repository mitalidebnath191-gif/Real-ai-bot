# Jarvis Telegram AI Bot (Serverless)

এটি একটি Professional Telegram AI Bot যা Vercel Serverless Functions-এ ডেপ্লয় করার জন্য তৈরি। এটি OpenRouter API ব্যবহার করে কাজ করে এবং প্রয়োজনে DuckDuckGo-এর মাধ্যমে Web Search করতে পারে।

## Features
- **Bilingual:** বাংলা এবং ইংরেজি সাপোর্ট করে।
- **Smart Web Search:** সাম্প্রতিক তথ্যের জন্য নিজে থেকেই ইন্টারনেট সার্চ করতে পারে।
- **Conversation History:** ইউজারের আগের কথা মনে রাখতে পারে।
- **Jarvis Personality:** প্রফেশনাল, স্মার্ট এবং ফ্রেন্ডলি।

## Deployment Guide (Vercel)

### Step 1: কোড আপলোড
1. আপনার GitHub-এ একটি নতুন Repository তৈরি করুন।
2. এই প্রজেক্টের ফাইলগুলো (`api/webhook.py`, `requirements.txt`, `vercel.json`) সেই রিপোজিটরিতে Push করুন।

### Step 2: Vercel এ Deploy করা
1. [Vercel](https://vercel.com)-এ লগইন করুন এবং **Add New Project**-এ ক্লিক করুন।
2. আপনার GitHub Repository-টি Import করুন।
3. **Environment Variables** সেকশনে গিয়ে নিচের দুটি Variable সেট করুন:
   - `BOT_TOKEN`: আপনার Telegram Bot-এর টোকেন (BotFather থেকে পাবেন)।
   - `OPENROUTER_API_KEY`: আপনার OpenRouter API Key।
4. **Deploy** বাটনে ক্লিক করুন। 

### Step 3: Telegram Webhook সেট করা
Vercel আপনাকে একটি URL দেবে (যেমন: `https://your-app-name.vercel.app`)। 
আপনার ব্রাউজারে নিচের URL-টি পেস্ট করুন এবং এন্টার চাপুন (ব্র্যাকেটের অংশগুলো নিজের তথ্য দিয়ে রিপ্লেস করবেন):

```text
[https://api.telegram.org/bot](https://api.telegram.org/bot)<YOUR_BOT_TOKEN>/setWebhook?url=https://<YOUR_VERCEL_URL>/api/webhook
