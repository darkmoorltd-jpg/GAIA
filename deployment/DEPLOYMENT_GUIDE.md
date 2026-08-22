# GAIA Production Deployment Guide

## Backend (FastAPI)

### Option 1: Railway (Easiest)
1. Push this repo to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Select this repo → Set Dockerfile path to `backend/Dockerfile`
4. Add environment variables from `backend/.env`
5. Deploy

### Option 2: Render
1. Go to render.com → New Web Service
2. Connect GitHub repo
3. Set Dockerfile path to `backend/Dockerfile`
4. Add environment variables
5. Deploy

### Option 3: DigitalOcean
1. Create Droplet (Ubuntu 22.04, 2GB RAM)
2. SSH in and install Docker
3. `git clone https://github.com/darkmoorltd-jpg/GAIA.git`
4. `cd GAIA/deployment && docker-compose up -d`

## Flutter App

### Build Android APK
```
cd flutter_app
flutter build apk --release
```

### Build iOS
```
cd flutter_app
flutter build ios --release
```

### Publish to Play Store
1. Create Google Play Developer account ($25)
2. Upload APK
3. Fill store listing
4. Publish