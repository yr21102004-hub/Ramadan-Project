# 🎨 Haj Ramadan Paints & Decor - CRM & Service Platform

![Project Banner](static/logo.webp)

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3-green.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple.svg?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Status](https://img.shields.io/badge/Status-Active-success.svg?style=for-the-badge)]()

**Haj Ramadan Paints & Decor** is a comprehensive web platform and Customer Relationship Management (CRM) system designed for a leading decoration and finishing company in Egypt. The platform bridges the gap between client service requests and operational management, offering a seamless experience from inquiry to project delivery.

---

## 🌟 Project Overview

This application serves two main purposes:
1.  **Marketing & Service Portal:** A high-performance, visually engaging website for customers to explore services, request inspections, and view portfolios.
2.  **Operational Dashboard (CRM):** A powerful admin interface for managing projects, tracking client progress, generating financial reports, and handling support tickets.

---

## 🚀 Key Features

### 👤 Customer Experience
*   **Dynamic Service Showcase:** Detailed sub-pages for Modern Paints, Gypsum Board, Wallpapers, and Restoration requests.
*   **Smart Booking System:** Context-aware contact forms that pre-select services based on user navigation.
*   **Client Dashboard:**
    *   **Live Progress Tracking:** Real-time progress bar (0% to 100%) for ongoing projects.
    *   **Project Timeline:** Visual steps tracking (Inspection -> Foundation -> Finishing -> Handover).
    *   **Support & Tickets:** Built-in ticketing system for complaints and inquiries.
*   **Visual Reviews:** Clients can rate completed projects and upload "Real Life" photos of the work.
*   **AI Chat Assistance:** Integrated chatbot for instant answers to common questions.
*   **Islamic Welcome Modal:** A unique, culturally tailored welcome animation on the first visit.

### 🛡️ Admin & Management Center
*   **Comprehensive Analytics Dashboard:** Real-time charts and data visualization for:
    *   User Growth & Engagement.
    *   Service Popularity.
    *   Financial Revenue Streams.
*   **Project Management:** Tools to update project percentages, assign statuses, and manage user data.
*   **Professional Reporting:**
    *   **Excel Export:** Detailed multi-sheet reports with auto-generated charts for financial and service analysis.
    *   **PDF Generation:** Instant generation of summary reports.
*   **Security Suite:**
    *   **Activity Logs:** Detailed tracking of all admin actions and system events.
    *   **Auto-Backup:** Automatic database backup system with manual override.
    *   **Traffic Monitoring:** Basic analytics on page views and visitor behavior.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **Backend** | Python 3.12 | Core logic and data processing |
| **Framework** | Flask | Lightweight WSGI web application framework |
| **Database** | SQLite | Serverless, self-contained relational database |
| **Frontend** | HTML5, CSS3, JS | Responsive design with **Bootstrap 5** |
| **Animations** | AOS & Custom CSS | Smooth scroll animations and loading effects |
| **Reporting** | OpenPyXL, ReportLab | Generating professional Excel & PDF reports |
| **Security** | Flask-Bcrypt | Password hashing and session protection |

---

## 📂 Project Structure

```bash
Ramadan-Project/
├── app.py                  # Application Entry Point
├── controllers/            # Logic Layer (Blueprints)
│   ├── admin_controller.py # Admin operational logic & reporting
│   ├── user_controller.py  # User dashboard & interactions
│   └── web_controller.py   # Public facing pages
├── models/                 # Database Models (SQLite Abstraction)
│   ├── database.py         # Base DB wrapper
│   └── ...                 # Specific models (User, Chat, Payment)
├── templates/              # Jinja2 HTML Templates
├── static/                 # Assets (CSS, JS, Images, Fonts)
├── utils/                  # Helper Utilities
│   └── export_helper.py    # Excel/PDF generation engine
└── requirements.txt        # Python Dependencies
```

---

## ⚙️ Installation & Setup

Follow these steps to run the project locally:

### 1. Clone the repository
```bash
git clone https://github.com/yr21102004-hub/Ramadan-Project.git
cd Ramadan-Project
```

### 2. Set up Virtual Environment (Recommended)
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

### 5. Access the Platform
Open your browser and navigate to: `http://127.0.0.1:5000`

---

## 📸 Usage Highlights

*   **Service Selection:** Navigate to any service page and click "Order Now" to see the smart form selection in action.
*   **Admin Access:** Login via `/auth/login` (Role: Admin) to access the Dashboard.
*   **Export Data:** Go to Admin Dashboard -> Analytics -> Export to download the enhanced Excel reports.

---

## 📞 Contact & Support

Developed by **Youssef (Smart Tech Solutions)**.  
For business inquiries or support, please contact: `ramadangaber01@gmail.com`

---
&copy; 2026 Haj Ramadan Paints & Decor. All rights reserved.
