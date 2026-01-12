# Quick Start Guide - Project Management Feature

## 🚀 Starting the Application

### Backend Server
```bash
cd backend
uvicorn app.main:app --reload
```
Server will run on: **http://localhost:8000**

### Frontend Server
```bash
cd frontend
npm run dev
```
Server will run on: **http://localhost:5173**

---

## 🌐 Access Points

- **Frontend App**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

---

## 👤 Test Accounts

### Existing User (with migrated photos)
- **Email**: olegandriichuk2004@gmail.com
- **Password**: [your password]
- **Has**: Default Project with existing photos

### Test User
- **Email**: test@example.com
- **Password**: test123

---

## 📋 Key Features

### Projects Page (`/projects`)
- ✅ Create new projects
- ✅ View all your projects with photo counts
- ✅ Delete projects (with confirmation)
- ✅ Open project to manage photos

### Project Workspace (`/projects/:id`)
- ✅ Upload photos (drag & drop or click)
- ✅ View uploaded photos in gallery
- ✅ Delete individual photos
- ✅ "Generate Stitched Image" button
- ✅ Back to Projects navigation

---

## 🗄️ Database Management

### Run Migrations
```bash
cd backend
alembic upgrade head
```

### Check Current Migration
```bash
alembic current
```

### Rollback Last Migration
```bash
alembic downgrade -1
```

### Create New Migration
```bash
alembic revision --autogenerate -m "description"
```

---

## 🔗 API Endpoints

### Authentication
```
POST /auth/register    - Register new user
POST /auth/login       - Login (returns JWT token)
GET  /auth/me          - Get current user info
```

### Projects
```
POST   /projects                 - Create project
GET    /projects                 - List user's projects
GET    /projects/{id}            - Get project details
DELETE /projects/{id}            - Delete project
```

### Photos (Project-Scoped)
```
POST   /projects/{id}/photos            - Upload photos
GET    /projects/{id}/photos            - List project photos
GET    /projects/{id}/photos/{photo_id} - Download photo
DELETE /projects/{id}/photos/{photo_id} - Delete photo
```

---

## 📊 Database Schema

```
User
 ├── id (UUID)
 ├── name
 ├── email (unique)
 ├── hashed_password
 └── created_at

Project
 ├── id (UUID)
 ├── user_id (FK → User)
 ├── name
 ├── description (optional)
 └── created_at

Photo
 ├── id (UUID)
 ├── user_id (FK → User)
 ├── project_id (FK → Project)
 ├── s3_key
 ├── original_name
 ├── mime
 ├── size
 └── created_at
```

**Relationships:**
- User 1→N Projects (cascade delete)
- Project 1→N Photos (cascade delete)
- User 1→N Photos (cascade delete)

---

## 🔒 Security

- **Authentication**: JWT tokens (30min expiry)
- **Authorization**: All endpoints check user ownership
- **Photo Access**: Triple check (user → project → photo)
- **CORS**: Configured for localhost:5173

---

## 🛠️ Troubleshooting

### Backend won't start
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

### Frontend won't start
```bash
cd frontend
npm install
npm run dev
```

### Database issues
```bash
# Backup first!
cp backend/app.db backend/app.db.backup

# Reset migrations
cd backend
alembic downgrade base
alembic upgrade head
```

### Port already in use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

---

## 📝 Development Notes

### Adding New Features
1. Backend changes → Create migration: `alembic revision --autogenerate -m "description"`
2. Apply migration: `alembic upgrade head`
3. Update frontend API clients
4. Test thoroughly!

### Code Structure
```
backend/
├── alembic/          # Database migrations
├── app/
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── repositories/ # Data access layer
│   ├── routers/      # API endpoints
│   ├── services/     # Business logic (S3, etc)
│   └── dependencies/ # FastAPI dependencies (auth)

frontend/
└── src/
    ├── api/          # API client functions
    ├── pages/        # Vue page components
    ├── router/       # Vue Router config
    └── stores/       # State management
```

---

## ✅ Checklist for Deployment

- [ ] Update `.env` with production settings
- [ ] Change JWT secret key
- [ ] Configure production database
- [ ] Update CORS origins
- [ ] Set up proper S3 bucket permissions
- [ ] Run migrations on production DB
- [ ] Build frontend: `npm run build`
- [ ] Test all features in production

---

## 📚 Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Vue 3 Docs**: https://vuejs.org
- **Vue Router**: https://router.vuejs.org
- **Alembic**: https://alembic.sqlalchemy.org
- **SQLAlchemy**: https://docs.sqlalchemy.org

---

**Last Updated**: January 6, 2026
**Status**: ✅ Fully Functional & Tested
