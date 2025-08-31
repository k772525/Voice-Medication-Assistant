#!/bin/bash
# GitHub Secrets 設置腳本 (Bash 版本) - 從 env.yaml 讀取版
# 此腳本協助您從 env.yaml 檔案讀取環境變數並設置為 GitHub Secrets

# 使用方式：
# 1. 確保您已安裝 GitHub CLI: https://cli.github.com/
# 2. 登入 GitHub CLI: gh auth login
# 3. 確保 env.yaml 檔案存在於專案根目錄
# 4. 給予腳本執行權限: chmod +x setup-github-secrets.sh
# 5. 執行腳本: ./setup-github-secrets.sh

# 定義 env.yaml 檔案路徑
ENV_YAML_PATH="./env.yaml"

echo "🔍 檢查系統需求..."

# 檢查是否安裝了 GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI 未安裝。請先安裝: https://cli.github.com/"
    exit 1
fi

# 檢查 env.yaml 檔案是否存在
if [ ! -f "$ENV_YAML_PATH" ]; then
    echo "❌ 找不到 env.yaml 檔案: $ENV_YAML_PATH"
    echo "請確保 env.yaml 檔案存在於專案根目錄"
    exit 1
fi

# 檢查是否已登入 GitHub
if ! gh auth status &> /dev/null; then
    echo "❌ 請先登入 GitHub CLI: gh auth login"
    exit 1
fi

echo "✅ 系統檢查完成，開始讀取 env.yaml 檔案..."

# 讀取並解析 env.yaml 檔案的函數
parse_yaml_value() {
    local line="$1"
    
    # 移除註解
    line=$(echo "$line" | cut -d'#' -f1)
    
    # 檢查是否包含冒號（key: value 格式）
    if [[ "$line" =~ ^[[:space:]]*([^:]+):[[:space:]]*(.*)$ ]]; then
        local key="${BASH_REMATCH[1]}"
        local value="${BASH_REMATCH[2]}"
        
        # 移除前後空格
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        # 移除引號
        value=$(echo "$value" | sed "s/^['\"]\\|['\"]$//g")
        
        # 跳過空值和註解行
        if [[ -n "$value" && -n "$key" && ! "$key" =~ ^# ]]; then
            echo "$key=$value"
        fi
    fi
}

# 讀取 env.yaml 檔案並解析環境變數
declare -A env_vars
var_count=0

while IFS= read -r line; do
    parsed=$(parse_yaml_value "$line")
    if [[ -n "$parsed" ]]; then
        key=$(echo "$parsed" | cut -d'=' -f1)
        value=$(echo "$parsed" | cut -d'=' -f2-)
        env_vars["$key"]="$value"
        ((var_count++))
    fi
done < "$ENV_YAML_PATH"

echo "📋 從 env.yaml 讀取到 $var_count 個環境變數"

# 定義需要設置的環境變數清單（按類別分組）
declare -A secret_categories

# LINE Bot API
linebot_vars="LINE_CHANNEL_ACCESS_TOKEN LINE_CHANNEL_SECRET YOUR_BOT_ID LINE_LOGIN_CHANNEL_ID LINE_LOGIN_CHANNEL_SECRET"

# Flask 應用程式
flask_vars="SECRET_KEY FLASK_ENV FLASK_DEBUG"

# LIFF 應用程式
liff_vars="LIFF_CHANNEL_ID LIFF_ID_CAMERA LIFF_ID_EDIT LIFF_ID_PRESCRIPTION_REMINDER LIFF_ID_MANUAL_REMINDER LIFF_ID_HEALTH_FORM"

# Google Cloud 服務
google_vars="GEMINI_API_KEY GEMINI_MODEL GCS_BUCKET_NAME GOOGLE_APPLICATION_CREDENTIALS SPEECH_TO_TEXT_ENABLED SPEECH_LANGUAGE_CODE SPEECH_ENCODING"

# 資料庫
db_vars="DB_HOST DB_USER DB_PASS DB_NAME DB_PORT DB_CHARSET DB_POOL_SIZE DB_POOL_TIMEOUT"

# 安全性
security_vars="REMINDER_SECRET_TOKEN API_RATE_LIMIT SESSION_TIMEOUT"

# 功能開關
feature_vars="VOICE_RECOGNITION_ENABLED AI_ANALYSIS_ENABLED FAMILY_MANAGEMENT_ENABLED HEALTH_MONITORING_ENABLED REMINDER_CHECK_INTERVAL MAX_REMINDERS_PER_USER REMINDER_ADVANCE_TIME AI_RESPONSE_TIMEOUT MAX_AI_REQUESTS_PER_HOUR"

# 日誌和監控
log_vars="LOG_LEVEL HEALTH_CHECK_ENABLED METRICS_ENABLED"

# 快取
cache_vars="CACHE_TYPE CACHE_DEFAULT_TIMEOUT"

# 應用程式環境
app_vars="APP_ENV APP_VERSION APP_NAME PORT HOST WORKERS WORKER_TIMEOUT"

# 除錯
debug_vars="DEBUG_MODE TESTING"

echo "🔐 開始設置 GitHub Secrets..."

total_secrets=0
success_count=0
skipped_count=0

# 設置 Secrets 的函數
set_secrets_for_category() {
    local category_name="$1"
    local category_vars="$2"
    
    echo ""
    echo "📂 設置 $category_name 相關 Secrets..."
    
    for var_name in $category_vars; do
        ((total_secrets++))
        
        if [[ -n "${env_vars[$var_name]}" ]]; then
            local value="${env_vars[$var_name]}"
            if [[ -n "$value" ]]; then
                if gh secret set "$var_name" --body "$value" &> /dev/null; then
                    echo "  ✅ $var_name"
                    ((success_count++))
                else
                    echo "  ❌ $var_name (設置失敗)"
                fi
            else
                echo "  ⚠️  $var_name (值為空，跳過)"
                ((skipped_count++))
            fi
        else
            echo "  ⚠️  $var_name (在 env.yaml 中未找到，跳過)"
            ((skipped_count++))
        fi
    done
}

# 按類別設置 Secrets
set_secrets_for_category "LINE Bot API" "$linebot_vars"
set_secrets_for_category "Flask 應用程式" "$flask_vars"
set_secrets_for_category "LIFF 應用程式" "$liff_vars"
set_secrets_for_category "Google Cloud 服務" "$google_vars"
set_secrets_for_category "資料庫" "$db_vars"
set_secrets_for_category "安全性" "$security_vars"
set_secrets_for_category "功能開關" "$feature_vars"
set_secrets_for_category "日誌和監控" "$log_vars"
set_secrets_for_category "快取" "$cache_vars"
set_secrets_for_category "應用程式環境" "$app_vars"
set_secrets_for_category "除錯" "$debug_vars"

echo ""
echo "📊 設置結果統計："
echo "  總共處理: $total_secrets 個環境變數"
echo "  成功設置: $success_count 個"
echo "  跳過設置: $skipped_count 個"

if [[ $success_count -eq $((total_secrets - skipped_count)) ]]; then
    echo "✅ 所有可用的 GitHub Secrets 設置完成！"
else
    echo "⚠️  部分 Secrets 設置可能失敗，請檢查上方日誌"
fi

echo ""
echo "📝 接下來您還需要手動設置以下 Workload Identity Federation 相關的 Secrets："
echo "   - WIF_PROVIDER (需要按照設置指南取得完整路徑)"
echo "   - WIF_SERVICE_ACCOUNT (github-actions-sa@gcp1-462701.iam.gserviceaccount.com)"
echo ""
echo "🔍 您可以使用以下指令檢查已設置的 secrets："
echo "   gh secret list"
echo ""
echo "🚀 設置完成後，您的 GitHub Actions workflow 就可以自動部署了！"