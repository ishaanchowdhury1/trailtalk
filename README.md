# 🥾 TrailTalk — Offline Nature Identifier & Walk Journal

> **Submission for Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass**  
> *Build something with open-weight models or open-source AI that gets people off the screen and into the world.*

---

## 🌟 What is TrailTalk?
**TrailTalk** is a privacy-first, 100% local nature identification and outdoor walk journal app designed for hikers, nature lovers, plant enthusiasts, and outdoor explorers.

When walking on remote forest trails or local parks with spotty or zero cellular signal, traditional cloud-based AI apps fail. TrailTalk solves this by running open-weight vision models (such as **Gemma 3** or **Llava**) locally via **Ollama**.

- **Take photos** of plants, trees, flowers, birds, or wildlife on the trail.
- **Get instant offline identification**, taxonomy details, ecological fun facts, and safety notes.
- **Log sightings automatically** to a local SQLite walk journal.
- **Export formatted summaries** to share your walk highlights on DEV.to!

---

## 🛠️ Tech Stack & Architecture

- **Frontend & UI**: Python, Streamlit
- **Open AI Engine**: Local Ollama with `gemma3:4b` / `llava` open vision models (with smart offline fallback engine for zero-setup testing)
- **Database**: SQLite3
- **Image Processing**: Pillow (PIL)
- **Data Export**: Pandas, Markdown

---

## 🚀 Quick Start Guide

### 1. Prerequisites & Installation

Make sure Python 3.9+ is installed. Clone/navigate to the directory and install dependencies:

```bash
cd trailtalk
pip install -r requirements.txt
```

### 2. (Optional but Recommended) Setup Local Ollama Model

For 100% local vision AI inference on your laptop:

1. Install [Ollama](https://ollama.com)
2. Pull the vision model:
```bash
ollama run gemma3:4b
```
*(Note: If Ollama is not running, TrailTalk automatically operates in **Smart Offline Engine Mode**, ensuring you can test and use the app immediately!)*

### 3. Launch the Application

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 🌿 Why Open Innovation Matters
1. **Zero Signal Required**: Runs 100% on local hardware on mountain trails, deep forests, or secluded parks without internet connection.
2. **Absolute Privacy**: Your photos, location notes, and trail routes never leave your personal computer or server.
3. **Zero API Cost**: No expensive proprietary vision API fees ($0/month forever).
4. **Model Swap Freedom**: Users can switch between Gemma 3, LLaVA, or fine-tuned custom botanical models freely.

---

## 📜 License
MIT License — Free to use, adapt, and build upon for open innovation!
