# 🔐 GitHub Secrets 自動設置指南

## 📋 概述

此專案提供了兩個自動化腳本，可以從 [`env.yaml`](./env.yaml) 檔案中讀取環境變數並自動設置為 GitHub Secrets。

## 📁 相關檔案

- [`env.yaml`](./env.yaml) - 環境變數配置檔案（47個變數）
- [`setup-github-secrets.ps1`](./setup-github-secrets.ps1) - PowerShell 版本腳本（Windows）
- [`setup-github-secrets.sh`](./setup-github-secrets.sh) - Bash 版本腳本（Linux/macOS）

## 🚀 快速開始

### Windows 用戶 (PowerShell)

```powershell
# 1. 安裝 GitHub CLI
winget install GitHub.cli

# 2. 登入 GitHub
gh auth login

# 3. 執行設置腳本
.\setup-github-secrets.ps1
```

### Linux/macOS 用戶 (Bash)

```bash
# 1. 安裝 GitHub CLI
# Ubuntu/Debian
sudo apt install gh

# macOS
brew install gh

# 2. 登入 GitHub
gh auth login

# 3. 給予執行權限並執行腳本
chmod +x setup-github-secrets.sh
./setup-github-secrets.sh
```

## 📊 腳本功能特色

### ✅ 智能化特性

- **動態讀取配置**：自動從 env.yaml 讀取最新的環境變數
- **分類管理**：按功能模組分類設置 Secrets
- **錯誤處理**：完整的錯誤檢查和狀態報告
- **統計報告**：顯示設置成功/失敗/跳過的詳細統計

### 🔍 系統檢查

腳本會自動檢查：
- ✅ GitHub CLI 是否已安裝
- ✅ 是否已登入 GitHub 帳號
- ✅ env.yaml 檔案是否存在
- ✅ 環境變數值是否有效

### 📂 支援的環境變數類別

| 類別 | 變數數量 | 說明 |
|------|----------|------|
| LINE Bot API | 5 | LINE 機器人基本配置 |
| Flask 應用程式 | 3 | Flask 框架配置 |
| LIFF 應用程式 | 6 | LINE 前端框架配置 |
| Google Cloud 服務 | 7 | Google 雲端服務配置 |
| 資料庫 | 8 | MySQL 資料庫配置 |
| 安全性 | 3 | 安全相關配置 |
| 功能開關 | 9 | 應用程式功能控制 |
| 日誌和監控 | 3 | 日誌和監控配置 |
| 快取 | 2 | 快取系統配置 |
| 應用程式環境 | 7 | 運行環境配置 |
| 除錯 | 2 | 開發和除錯配置 |

## 📝 手動設置項目

腳本執行完成後，您還需要手動設置以下 Workload Identity Federation 相關的 Secrets：

- `WIF_PROVIDER` - Workload Identity Provider 完整路徑
- `WIF_SERVICE_ACCOUNT` - 服務帳號電子郵件

詳細設置方法請參考 [`DEPLOYMENT_SETUP_GUIDE.md`](./DEPLOYMENT_SETUP_GUIDE.md)

## 🔍 驗證設置

```bash
# 查看已設置的 Secrets
gh secret list

# 檢查特定 Secret
gh secret list | grep "SECRET_NAME"
```

## ⚠️ 注意事項

1. **敏感資料保護**：請確保 env.yaml 檔案不會被提交到公開的版本控制系統
2. **定期更新**：建議定期更新 API 金鑰和密碼
3. **權限管理**：確保只有必要的人員能夠存取 GitHub Secrets
4. **備份重要**：建議備份重要的配置資訊

## 🆘 故障排除

### 常見問題

**問題：GitHub CLI 未安裝**
```
❌ GitHub CLI 未安裝。請先安裝: https://cli.github.com/
```
**解決方案**：按照提示安裝 GitHub CLI

**問題：找不到 env.yaml 檔案**
```
❌ 找不到 env.yaml 檔案
```
**解決方案**：確保在專案根目錄執行腳本，且 env.yaml 檔案存在

**問題：未登入 GitHub**
```
❌ 請先登入 GitHub CLI: gh auth login
```
**解決方案**：執行 `gh auth login` 並完成認證流程

## 📞 技術支援

如果您在使用過程中遇到問題，請：

1. 檢查 [故障排除](#故障排除) 章節
2. 查看腳本輸出的錯誤訊息
3. 確認所有前置需求都已滿足
4. 聯繫技術支援團隊

---

🎉 **恭喜！** 完成設置後，您的 GitHub Actions workflow 就可以自動部署到 Google Cloud Run 了！