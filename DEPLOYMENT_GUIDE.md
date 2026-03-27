# YojanaIQ Deployment Guide 🚀

Your codebase is now professionally structured for cloud deployment! I have decoupled your React frontend from your Python backend and generated a production Docker environment.

Here is exactly how you launch it to the world for free:

---

## Step 1: Push your code to GitHub
To use Vercel or Render, your code must be on GitHub.
1. Create a new repository on [GitHub](https://github.com).
2. Push your `ap_scheme_rag` folder.

> **WARNING:** Before pushing, ensure your `.env` file is in a `.gitignore` so you do not accidentally publish your `GROQ_API_KEY` or `TELEGRAM_BOT_TOKEN` to the public internet!

---

## Step 2: Deploy Backend to Render (or Railway)
Your FastAPI web service and Telegram bot must run simultaneously. I have crafted a `Dockerfile` and `start.sh` to do exactly this automatically!

1. Go to [Render.com](https://render.com) and click **New > Web Service**.
2. Connect your GitHub repository.
3. Render will auto-detect the `Dockerfile` I made for you!
4. Go to the **Environment Variables** tab and paste:
   - `GROQ_API_KEY` = *(your key)*
   - `TELEGRAM_BOT_TOKEN` = *(your key)*
5. Click **Deploy**. 

> **TIP:** Once it finishes booting, Render will give you a public URL (e.g. `https://yojanaiq-api.onrender.com`). **Copy this URL**, you need it for Step 3!

---

## Step 3: Deploy Frontend to Vercel
Your React app needs to know where the new Python server lives.

1. Go to [Vercel.com](https://vercel.com) and click **Add New Project**.
2. Connect your GitHub repository.
3. Critically, change the **Root Directory** to `frontend` so Vercel knows where the React code is.
4. Open the **Environment Variables** dropdown and add:
   - **Name**: `VITE_API_URL`
   - **Value**: *(The Render URL you copied in Step 2, e.g. `https://yojanaiq-api.onrender.com`)*
5. Click **Deploy**.

**Congratulations!** 🎉 
Your AI application is now fully decoupled, Dockerized, and deployed to the internet, and your Telegram bot will wake up and start answering messages 24/7!
