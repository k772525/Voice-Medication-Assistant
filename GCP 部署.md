# GCP 部署

### 1️⃣ 啟用 API（直接一行執行）

```
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
```

---

### 2️⃣ 建立 Artifact Registry

```
gcloud artifacts repositories create pill_test --repository-format=docker --location=us-central1
```

> ⚠️ 如果你已經建立過，可以略過此步驟。會出現 ALREADY_EXISTS 也沒關係。
> 

---

### 3️⃣ 設定 Docker 認證

```
gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

### 4️⃣ 建立 Docker Image 並推送

```
set PROJECT_ID=gcp1-462701
docker build -t us-central1-docker.pkg.dev/gcp1-462701/pill-test/linebot0725:latest .
docker push us-central1-docker.pkg.dev/gcp1-462701/pill-test/linebot0725:latest
```

``
gcloud run deploy linebot0725 --image=us-central1-docker.pkg.dev/gcp1-462701/pill-test/linebot0725:latest --region=us-central1 --platform=managed --allow-unauthenticated --env-vars-file=env.yaml --min-instances=1 --memory=4Gi --timeout=300s

### 4. 設定 Cloud Scheduler
```bash
# 啟用 Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com

# 創建 App Engine 應用（如果尚未創建）
gcloud app create --region=us-central1

# 創建排程任務
gcloud scheduler jobs create http reminder-check-jobreminder-check-job --location=us-central1 --schedule="* * * * *" --uri="https://linebot0725-712800774423.us-central1.run.app/api/check-reminders" --http-method=POST --headers="Content-Type=application/json,Authorization=Bearer 9a8b7c6d5e4f321abc999888777" --description="每分鐘檢查並發送用藥提醒" --time-zone="Asia/Taipei"


