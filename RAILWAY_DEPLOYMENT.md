# 🚀 Railway Deployment Guide

## Quick Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/brain-stroke-prediction)

## Manual Deployment Steps

### 1. **Create Railway Account**
- Go to [railway.app](https://railway.app)
- Sign up with GitHub account

### 2. **Deploy from GitHub**
1. Click "New Project" in Railway dashboard
2. Select "Deploy from GitHub repo"
3. Choose `valueblime-hash/brain-ml` repository
4. Railway will automatically detect the configuration

### 3. **Environment Variables**
Railway will automatically set these variables:
- `FLASK_ENV=production`
- `PYTHONPATH=/app/backend:/app/ml-model`
- `FORCE_SQLITE=true`

### 4. **Deployment Process**
Railway will:
1. Install Python dependencies
2. Install Node.js dependencies
3. Build React frontend
4. Copy frontend build to backend static folder
5. Start the Flask server

### 5. **Access Your App**
- Railway will provide a URL like: `https://brain-ml-production-xxxx.up.railway.app`
- The app serves both API and frontend from the same domain

## Project Structure for Railway

```
brain-ml/
├── backend/           # Flask API
├── frontend/          # React App
├── ml-model/          # ML Models
├── start.py          # Railway entry point
├── requirements.txt   # Python dependencies
├── railway.toml      # Railway configuration
├── nixpacks.toml     # Build configuration
└── Procfile          # Process configuration
```

## API Endpoints

Once deployed, your API will be available at:
- `GET /` - Health check
- `POST /api/predict` - Stroke prediction
- `POST /api/auth/login` - User authentication
- `GET /api/history` - Prediction history

## Frontend Features

The deployed app includes:
- 🧠 AI-powered stroke risk assessment
- 👤 User authentication and profiles
- 📊 Interactive dashboard with charts
- 📱 Mobile-responsive design
- 🔒 Password visibility toggles (newly added!)

## Demo Credentials

- **Email**: `demo@strokeprediction.com`
- **Password**: `demo123`

## Troubleshooting

### Build Issues
- Check Railway build logs
- Ensure all dependencies are in requirements.txt
- Verify Node.js version compatibility

### Runtime Issues
- Check Railway deployment logs
- Verify environment variables
- Test API endpoints individually

## Support

- 📧 GitHub Issues: [Create Issue](https://github.com/valueblime-hash/brain-ml/issues)
- 📚 Documentation: See README.md
- 🚀 Railway Docs: [railway.app/docs](https://docs.railway.app)

---

**🎉 Your Brain Stroke Prediction System is now ready for Railway deployment!**