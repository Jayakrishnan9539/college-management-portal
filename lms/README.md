# 🎓 Landmine Soft — College Management Portal (LMS)

A full-stack college management system built with **Django REST Framework**, **MySQL**, and **React.js**.

---

## 🗂 Project Structure

```
lms/
├── backend/               # Django REST Framework API
│   ├── config/            # Settings, URLs, WSGI
│   ├── apps/
│   │   ├── users/         # Auth, Student, Faculty, Admin profiles
│   │   ├── courses/       # Subjects, Courses, Enrollments
│   │   ├── attendance/    # Class attendance tracking
│   │   ├── marks/         # Marks entry & grade calculation
│   │   ├── fees/          # Fee structures & payment recording
│   │   └── announcements/ # College notices
│   ├── manage.py
│   └── requirements.txt
│
└── frontend/              # React.js app
    ├── public/
    └── src/
        ├── api/           # Axios client & all API calls
        ├── context/       # AuthContext (JWT state)
        ├── components/    # Shared layout (sidebar, header)
        └── pages/         # Student, Faculty, Admin pages
```

---

## ⚙️ Backend Setup (Django + MySQL)

### 1. Prerequisites
- Python 3.10+
- MySQL 8.0+
- pip

### 2. Create MySQL database

```sql
CREATE DATABASE lms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Create virtual environment & install dependencies

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your MySQL credentials:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=lms_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
```

### 5. Run migrations & create superadmin

```bash
python manage.py makemigrations users courses attendance marks fees announcements
python manage.py migrate
python manage.py createsuperuser
```

> **Note:** The superuser command creates a Django admin user. To create the first LMS Admin, use the Django admin panel at `/admin/` or run:
> ```python
> from apps.users.models import User, Admin
> u = User.objects.create_user(email='admin@lms.edu', password='Admin@123', name='Super Admin', role='ADMIN', is_staff=True)
> Admin.objects.create(user=u, admin_role='SuperAdmin')
> ```

### 6. Start the backend server

```bash
python manage.py runserver
```

API runs at: **http://localhost:8000**  
Swagger docs: **http://localhost:8000/swagger/**

---

## 🖥 Frontend Setup (React.js)

### 1. Prerequisites
- Node.js 18+
- npm or yarn

### 2. Install dependencies & start

```bash
cd frontend
npm install
npm start
```

App runs at: **http://localhost:3000**

> The frontend proxies API requests to `http://localhost:8000` automatically via `"proxy"` in `package.json`.

---

## 🔐 API Overview

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/student/register` | Student self-registration |
| POST | `/api/auth/student/login` | Student login → returns JWT |
| POST | `/api/auth/faculty/login` | Faculty login |
| POST | `/api/auth/admin/login` | Admin login |
| POST | `/api/auth/forgot-password` | Send password reset email |
| POST | `/api/auth/reset-password` | Reset with token |
| POST | `/api/auth/change-password` | Change password (JWT required) |

### Student
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/PUT | `/api/student/profile` | View / update profile |
| GET/POST | `/api/courses/enrollments` | View enrollments / enroll |
| DELETE | `/api/courses/enrollments/<id>` | Drop a course |
| GET | `/api/attendance/my` | View own attendance |
| GET | `/api/marks/my` | View own marks & CGPA |
| GET | `/api/fees/my` | View fee status |
| POST | `/api/fees/pay` | Record fee payment |

### Faculty
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/faculty/profile` | View profile |
| GET | `/api/courses/my-courses` | View assigned courses |
| POST | `/api/attendance/mark` | Mark attendance (bulk) |
| GET/POST | `/api/marks/course/<id>` | View / enter marks |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/dashboard` | Dashboard stats |
| GET/PUT/DELETE | `/api/admin/students/<id>` | Manage students |
| GET | `/api/admin/faculty` | List faculty |
| POST/GET | `/api/courses/subjects` | Subject management |
| POST/GET | `/api/courses/` | Course assignment |
| POST/GET | `/api/fees/structures` | Fee structure management |
| GET | `/api/fees/admin/report` | Fee collection report |
| POST/GET | `/api/announcements` | Post / view announcements |

---

## 👥 User Roles

| Role | Access |
|------|--------|
| **STUDENT** | Self-registration, view own data, enroll, pay fees |
| **FACULTY** | Mark attendance, enter marks, view own courses |
| **ADMIN** | Full access — manage students, faculty, courses, fees, announcements |

---

## 🎓 Grade Scale

| Grade | Points | Percentage |
|-------|--------|------------|
| A+ | 10 | 90–100% |
| A | 9 | 80–89% |
| B+ | 8 | 70–79% |
| B | 7 | 60–69% |
| C | 6 | 50–59% |
| D | 5 | 40–49% |
| F | 0 | Below 40% |

---

## 🚀 Deployment (Render)

### Backend
1. Push code to GitHub
2. Create a new **Web Service** on Render
3. Build command: `pip install -r requirements.txt && python manage.py migrate`
4. Start command: `gunicorn config.wsgi:application`
5. Add environment variables from `.env`

### Frontend
1. Build: `npm run build`
2. Deploy the `build/` folder to **Vercel** or **Netlify**
3. Set `REACT_APP_API_URL` to your Render backend URL

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10, Django 4.2, DRF 3.14 |
| Auth | JWT (djangorestframework-simplejwt) |
| Database | MySQL 8.0 (via mysqlclient) |
| Frontend | React 18, React Router v6 |
| HTTP Client | Axios |
| API Docs | Swagger (drf-yasg) |
| Deployment | Render (backend), Vercel (frontend) |

---

*Built for Landmine Soft — Assignment LMS/S1/001*
