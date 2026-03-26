# Smart Campus Assistant 🎓

A modern, highly interactive, and intelligent campus management system with an integrated AI Chatbot. Built to handle academic tracking, library management, fee details, attendance, and instant student queries using large language models.

## 🌟 Features
* **AI-Powered Chatbot:** Context-aware assistant utilizing the Groq API (LLaMA 3) to answer student-specific and general campus queries.
* **Role-Based Dashboards:** Dedicated, secure interfaces for Students and Administrators.
* **Student Tracking:** Monitor attendance, grades, fee dues, and library book loans.
* **Modern UI/UX:** Responsive, 3D glassmorphism aesthetics with dynamic animations.
* **Admin Controls:** Comprehensive CRUD operations to manage student records seamlessly.

## 🛠 Tech Stack
* **Frontend:** HTML5, CSS3, JavaScript
* **Backend:** Python, Flask
* **Database:** SQLite
* **AI Integration:** Groq API (`llama-3.3-70b-versatile`)
* **Localization:** Google Translator (via `deep-translator`)

## 🚀 Running the Project Locally

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/Smart-campus-query-assistant.git
cd Smart-campus-query-assistant
```

### 2. Set up a virtual environment (Recommended)
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the template environment file to create your own configuration:
```bash
cp .env.example .env
```
Edit the newly created `.env` file and replace the placeholder values with your actual secrets. **Never commit the `.env` file to version control.**

### 5. Initialize the database
*(If not already present)*
```bash
python create_db.py
python setup_chat_db.py
```

### 6. Run the application
```bash
python app.py
```
Visit `http://localhost:5000` in your browser. Admin users can log in based on the configuration set in your database.

## ☁️ Deployment (Render)

This application is ready to be deployed on [Render](https://render.com/).

1. Create a new **Web Service** on Render and connect your GitHub repository.
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `gunicorn app:app` *(Make sure to add `gunicorn` to your requirements.txt)*
4. **Environment Variables:** In the Render dashboard, go to the "Environment" tab and add the variables listed in `.env.example` (e.g., `GROQ_API_KEY`, `SECRET_KEY`).

## 📸 Screenshots
*(Replace these placeholder links with actual paths to your screenshots)*
| Login Interface | Student Dashboard | Admin Dashboard |
| :---: | :---: | :---: |
| ![Login](link_to_screenshot) | ![Student](link_to_screenshot) | ![Admin](link_to_screenshot) |
