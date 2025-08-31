# GCP 部署和 Cloud Scheduler 設置指南

## 🎆 自動化部署狀態

✅ **GitHub Actions CI/CD**: 已完成設置並正常運行  
✅ **Cloud Run 部署**: 自動部署到 `linebot0831`  
✅ **環境變數**: 26個 GitHub Secrets 已設置  
⚠️ **Cloud Scheduler**: 需要手動設置權限  

---

## 🔄 自動部署流程

每當您推送代碼到 `main` 分支時，GitHub Actions 會自動：

1. 建置 Docker 映像
2. 推送到 Artifact Registry
3. 部署到 Cloud Run (`linebot0831`)
4. 嘗試設置 Cloud Scheduler（需要權限）

**服務 URL**: https://linebot0831-q36inpkvxa-uc.a.run.app

---

## 🕰 手動設置 Cloud Scheduler

由於權限限制，需要手動設置用藥提醒的排程任務：

### 1️⃣ 啟用必要的 API

```bash
# 啟用 Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com

# 啟用 App Engine Admin API（如果需要）
gcloud services enable appengine.googleapis.com
```

### 2️⃣ 創建 App Engine 應用（如果尚未創建）

```bash
# 檢查是否已存在
gcloud app describe

# 如果不存在，創建 App Engine 應用
gcloud app create --region=us-central1
```

### 3️⃣ 創建用藥提醒排程任務

```bash
# 刪除舊的任務（如果存在）
gcloud scheduler jobs delete reminder-check-job --location=us-central1 --quiet

# 創建新的排程任務
gcloud scheduler jobs create http reminder-check-job \
  --location=us-central1 \
  --schedule="* * * * *" \
  --uri="https://linebot0831-q36inpkvxa-uc.a.run.app/api/check-reminders" \
  --http-method=POST \
  --headers="Content-Type=application/json,Authorization=Bearer 9a8b7c6d5e4f321abc999888777" \
  --description="每分鐘檢查並發送用藥提醒" \
  --time-zone="Asia/Taipei"
```

### 4️⃣ 驗證設置

```bash
# 查看排程任務
gcloud scheduler jobs list --location=us-central1

# 查看任務詳情
gcloud scheduler jobs describe reminder-check-job --location=us-central1

# 手動觸發測試
gcloud scheduler jobs run reminder-check-job --location=us-central1
```

---

## 🔍 故障排除

### 常見問題

**問題**: `PERMISSION_DENIED` 錯誤
**解決**: 確保您的 Google Cloud 帳號有以下角色：
- Cloud Scheduler Admin
- App Engine Admin
- Service Usage Admin

**問題**: App Engine 應用創建失敗
**解決**: 檢查配額限制，確保選擇正確的區域

**問題**: 排程任務不執行
**解決**: 檢查服務 URL 是否正確，檢查認證 Token

### 檢查日誌

```bash
# 查看 Cloud Scheduler 日誌
gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=reminder-check-job" --limit=10

# 查看 Cloud Run 日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=linebot0831" --limit=10
```

---

## 🔄 後續維護

### 更新應用程式
1. 修改代碼並推送到 `main` 分支
2. GitHub Actions 會自動重新部署
3. Cloud Scheduler 會自動使用新的服務 URL

### 修改排程頻率
```bash
# 修改為每 5 分鐘檢查一次
gcloud scheduler jobs update http reminder-check-job \
  --location=us-central1 \
  --schedule="*/5 * * * *"
```

### 暫停/恢復排程
```bash
# 暫停
gcloud scheduler jobs pause reminder-check-job --location=us-central1

# 恢復
gcloud scheduler jobs resume reminder-check-job --location=us-central1
```