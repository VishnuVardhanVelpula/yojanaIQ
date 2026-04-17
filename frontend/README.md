# 🌐 YojanaIQ Frontend

The user-facing web portal for YojanaIQ, built with **React** and **Vite**. It features a premium, responsive design that guides users through the welfare scheme discovery process.

---

## 🛠️ Tech Stack

- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **State Management**: React Hooks (Context API)
- **Deployment**: Optimized for Vercel

---

## 🚀 Getting Started

### 1. Environment Configuration

Create a `.env` file in this directory (or copy from `.env.example`):

```env
VITE_API_URL=http://localhost:8000
```

- For local development, point this to your local FastAPI server.
- For production, point this to your deployed Render/Railway URL.

### 2. Development

```bash
# Install dependencies
npm install

# Start the dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

### 3. Production Build

```bash
npm run build
```

The production-ready assets will be generated in the `dist/` folder.

---

## 🎨 UI/UX Design

The frontend implements a high-contrast dark theme designed for accessibility and clarity. It uses a step-by-step modular form to collect user eligibility data without overwhelming the interface.

---

## 📦 Deployment to Vercel

1. Connect this repository to Vercel.
2. Set the **Root Directory** to `frontend`.
3. Add the `VITE_API_URL` environment variable.
4. Deploy!
