# 🚀 Railway Deployment Guide - Separate Services

## Overview

Railway requires **separate services** for Python backend and Node.js frontend. This guide shows you how to deploy both services and connect them properly.

## 🏗️ **Architecture**

```
Railway Project: brain-ml
├── 🐍 Backend Service (Python/Flask)
│   ├── URL: https://backend-production-xxxx.up.railway.app
│   └── Serves: API endpoints only
└── ⚛️ Frontend Service (Node.js/React)
    ├── URL: https://frontend-production-xxxx.up.railway.app
    └── Serves: React app + static files
```

## 📋 **Step-by-Step Deployment**

### **Step 1: Deploy Backend Service**

1. **Go to Railway Dashboard**
   - Visit [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `valueblime-hash/brain-ml`

2. **Configure Backend Service**
   - **Root Directory**: `/backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

3. **Set Environment Variables**
   ```
   FLASK_ENV=production
   PYTHONPATH=/app/backend:/app/ml-model
   FORCE_SQLITE=true
   SECRET_KEY=your-secret-key-here
   PORT=5000
   ```

4. **Deploy Backend**
   - Railway will build and deploy the Flask API
   - Note the backend URL: `https://backend-production-xxxx.up.railway.app`

### **Step 2: Deploy Frontend Service**

1. **Add New Service to Same Project**
   - In Railway dashboard, click "Add Service"
   - Select "GitHub Repo" again
   - Choose the same `valueblime-hash/brain-ml` repository

2. **Configure Frontend Service**
   - **Root Directory**: `/frontend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`

3. **Set Environment Variables**
   ```
   REACT_APP_API_URL=https://backend-production-xxxx.up.railway.app
   NODE_ENV=production
   GENERATE_SOURCEMAP=false
   ```

4. **Deploy Frontend**
   - Railway will build React app and serve it
   - Note the frontend URL: `https://frontend-production-xxxx.up.railway.app`

## 🔧 **Configuration Files Needed**

### **Backend Configuration**

Create `backend/railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "deploy": {
    "startCommand": "python app.py",
    "healthcheckPath": "/",
    "healthcheckTimeout": 100
  }
}
```

### **Frontend Configuration**

Create `frontend/railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "deploy": {
    "startCommand": "npm start",
    "healthcheckPath": "/",
    "healthcheckTimeout": 100
  }
}
```

## 🌐 **Alternative: Backend-Only Deployment with Static Frontend**

If you prefer a single service, you can serve the React build from Flask:

### **Option A: Flask Serves Everything**

1. **Build Frontend Locally**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Copy Build to Backend**
   ```bash
   cp -r frontend/build/* backend/static/
   ```

3. **Update Flask App** to serve static files:
   ```python
   from flask import Flask, send_from_directory
   
   app = Flask(__name__, static_folder='static', static_url_path='')
   
   @app.route('/')
   def serve_frontend():
       return send_from_directory(app.static_folder, 'index.html')
   
   @app.route('/<path:path>')
   def serve_static(path):
       return send_from_directory(app.static_folder, path)
   ```

4. **Deploy Only Backend**
   - Root Directory: `/backend`
   - Railway serves both API and frontend from Flask

## 📊 **Recommended Approach: Separate Services**

### **Pros:**
- ✅ Better separation of concerns
- ✅ Independent scaling
- ✅ Easier debugging
- ✅ Better performance

### **Cons:**
- ❌ Two separate URLs
- ❌ CORS configuration needed
- ❌ Slightly more complex setup

## 🔒 **CORS Configuration**

For separate services, update your Flask backend:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['https://frontend-production-xxxx.up.railway.app'])
```

## 🧪 **Testing Your Deployment**

### **Backend Testing**
```bash
curl https://backend-production-xxxx.up.railway.app/
curl https://backend-production-xxxx.up.railway.app/api/info
```

### **Frontend Testing**
- Visit: `https://frontend-production-xxxx.up.railway.app`
- Test login with demo credentials
- Verify API calls work

## 🚨 **Common Issues & Solutions**

### **CORS Errors**
- Add frontend URL to CORS origins in backend
- Verify REACT_APP_API_URL points to correct backend

### **Build Failures**
- Check Node.js version compatibility
- Verify all dependencies in package.json
- Check Railway build logs

### **API Connection Issues**
- Verify backend is deployed and healthy
- Check environment variables
- Test API endpoints directly

## 📱 **Demo Credentials**

Once deployed, test with:
- **Email**: `demo@strokeprediction.com`
- **Password**: `demo123`

## 🎯 **Final URLs**

After successful deployment:
- **Main App**: `https://frontend-production-xxxx.up.railway.app`
- **API**: `https://backend-production-xxxx.up.railway.app`
- **Health Check**: `https://backend-production-xxxx.up.railway.app/`

---

**🎉 This approach ensures reliable deployment on Railway with proper separation of services!**