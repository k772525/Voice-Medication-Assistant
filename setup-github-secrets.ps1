# GitHub Secrets 設置腳本 (PowerShell 版本) - 從 env.yaml 讀取版
# 此腳本協助您從 env.yaml 檔案讀取環境變數並設置為 GitHub Secrets

# 使用方式：
# 1. 確保您已安裝 GitHub CLI: https://cli.github.com/
# 2. 登入 GitHub CLI: gh auth login
# 3. 確保 env.yaml 檔案存在於專案根目錄
# 4. 在 PowerShell 中執行此腳本: .\setup-github-secrets.ps1

# 定義 env.yaml 檔案路徑
$envYamlPath = "C:\Users\k7725\Desktop\cicd-test\Voice-Medication-Assistant\env.yaml"

Write-Host "🔍 檢查系統需求..." -ForegroundColor Yellow

# 檢查是否安裝了 GitHub CLI
if (-not (Test-Path "C:\Program Files\GitHub CLI\gh.exe")) {
    Write-Host "❌ GitHub CLI 未安裝。請先安裝: https://cli.github.com/" -ForegroundColor Red
    exit 1
}

# 檢查 env.yaml 檔案是否存在
if (-not (Test-Path $envYamlPath)) {
    Write-Host "❌ 找不到 env.yaml 檔案: $envYamlPath" -ForegroundColor Red
    Write-Host "請確保 env.yaml 檔案存在於指定路徑" -ForegroundColor Red
    exit 1
}

# 檢查是否已登入 GitHub
try {
    & "C:\Program Files\GitHub CLI\gh.exe" auth status 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 請先登入 GitHub CLI: gh auth login" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ 請先登入 GitHub CLI: gh auth login" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 系統檢查完成，開始讀取 env.yaml 檔案..." -ForegroundColor Green

# 讀取並解析 env.yaml 檔案的函數
function Parse-YamlValue {
    param(
        [string]$line
    )
    
    # 移除註解
    $line = $line -split '#' | Select-Object -First 1
    
    # 檢查是否包含冒號（key: value 格式）
    if ($line -match '^\s*([^:]+):\s*(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        
        # 移除引號
        $value = $value.Trim("'").Trim('"')
        
        # 跳過空值和註解行
        if ($value -and $key -and -not $key.StartsWith('#')) {
            return @{
                Key = $key
                Value = $value
            }
        }
    }
    
    return $null
}

# 讀取 env.yaml 檔案並解析環境變數
$envVars = @{}
$content = Get-Content $envYamlPath -Encoding UTF8

foreach ($line in $content) {
    $parsed = Parse-YamlValue $line
    if ($parsed) {
        $envVars[$parsed.Key] = $parsed.Value
    }
}

Write-Host "📋 從 env.yaml 讀取到 $($envVars.Count) 個環境變數" -ForegroundColor Cyan

# 定義需要設置的環境變數列表
$secrets = @(
    "LINE_CHANNEL_ACCESS_TOKEN",
    "LINE_CHANNEL_SECRET", 
    "YOUR_BOT_ID",
    "LINE_LOGIN_CHANNEL_ID",
    "LINE_LOGIN_CHANNEL_SECRET",
    "SECRET_KEY",
    "LIFF_CHANNEL_ID",
    "LIFF_ID_CAMERA",
    "LIFF_ID_EDIT",
    "LIFF_ID_PRESCRIPTION_REMINDER",
    "LIFF_ID_MANUAL_REMINDER",
    "LIFF_ID_HEALTH_FORM",
    "GEMINI_API_KEY",
    "GCS_BUCKET_NAME",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "SPEECH_TO_TEXT_ENABLED",
    "SPEECH_LANGUAGE_CODE",
    "DB_HOST",
    "DB_USER",
    "DB_PASS",
    "DB_NAME",
    "DB_PORT",
    "REMINDER_SECRET_TOKEN",
    "YOLO_V12_URL",
    "YOLO_V11_URL",
    "KEVIN_API_URL"
)

Write-Host "🔐 開始設置 GitHub Secrets..." -ForegroundColor Green

$totalSecrets = 0
$successCount = 0
$skippedCount = 0

# 設置每個 Secret
foreach ($secretName in $secrets) {
    $totalSecrets++
    
    if ($envVars.ContainsKey($secretName)) {
        $value = $envVars[$secretName]
        if ($value) {
            try {
                & "C:\Program Files\GitHub CLI\gh.exe" secret set $secretName --body $value
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  ✅ $secretName" -ForegroundColor Green
                    $successCount++
                } else {
                    Write-Host "  ❌ $secretName (設置失敗)" -ForegroundColor Red
                }
            } catch {
                Write-Host "  ❌ $secretName (設置失敗: $($_.Exception.Message))" -ForegroundColor Red
            }
        } else {
            Write-Host "  ⚠️  $secretName (值為空，跳過)" -ForegroundColor Yellow
            $skippedCount++
        }
    } else {
        Write-Host "  ⚠️  $secretName (在 env.yaml 中未找到，跳過)" -ForegroundColor Yellow
        $skippedCount++
    }
}

Write-Host ""
Write-Host "📊 設置結果統計：" -ForegroundColor Magenta
Write-Host "  總共處理: $totalSecrets 個環境變數" -ForegroundColor White
Write-Host "  成功設置: $successCount 個" -ForegroundColor Green
Write-Host "  跳過設置: $skippedCount 個" -ForegroundColor Yellow

if ($successCount -eq ($totalSecrets - $skippedCount)) {
    Write-Host "✅ 所有可用的 GitHub Secrets 設置完成！" -ForegroundColor Green
} else {
    Write-Host "⚠️  部分 Secrets 設置可能失敗，請檢查上方日誌" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📝 接下來您還需要手動設置以下 Workload Identity Federation 相關的 Secrets：" -ForegroundColor Yellow
Write-Host "   - WIF_PROVIDER (需要按照設置指南取得完整路徑)" -ForegroundColor White
Write-Host "   - WIF_SERVICE_ACCOUNT (github-actions-sa@gcp1-462701.iam.gserviceaccount.com)" -ForegroundColor White
Write-Host ""
Write-Host "🔍 您可以使用以下指令檢查已設置的 secrets：" -ForegroundColor Yellow
Write-Host "   'C:\Program Files\GitHub CLI\gh.exe' secret list" -ForegroundColor White
Write-Host ""
Write-Host "🚀 設置完成後，您的 GitHub Actions workflow 就可以自動部署了！" -ForegroundColor Green