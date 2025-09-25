# 🏠 HomeAR

Built by **Janesh Kapoor**

---

## 🖥️ Server (Flask Backend)

### Overview
The backend server for HomeAR, built with **Flask** and **Together AI APIs**.  
It powers the AI-driven image generation, default variations, and chat-with-image functionality.

### Features
- Accepts photo uploads from the mobile app  
- Generates **3 design variations** by default using Together AI  
- Supports **custom text prompts** to edit existing images  
- Provides a **chat-with-image** endpoint for iterative editing  
- Handles concurrency safely with thread locks  
- Serves uploaded and generated images via Flask routes  

### Tech Stack
- Python 3.9+  
- Flask (REST API framework)  
- Together AI (Flux model for image generation)  
- Werkzeug (file handling utilities)  

### Setup Instructions
1. Clone the repository  
   ```bash
   git clone https://github.com/JaneshKapoor/kontext-homear
   cd server
   ```

2.  Create virtual environment
    python3 -m venv venv
    source venv/bin/activate   # Mac/Linux
    venv\Scripts\activate      # Windows

3. Install dependencies
    pip install -r requirements.txt

4. Run the server
    python server.py


Server runs at: http://0.0.0.0:3000

API Endpoints

POST /multi-upload → Upload an image, get 3 AI-generated design variations

POST /upload → Apply a custom edit with text prompt

POST /chat-with-image → Iteratively edit a specific generated image

GET /uploads/<file> → Access uploaded/generated images