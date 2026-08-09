$dirs = @(
  "docs\images\ui_mockups", "docs\images\architecture", "docs\images\diagrams", "docs\images\screenshots",
  "frontend\public\assets",
  "frontend\src\api", "frontend\src\assets", "frontend\src\components\common", "frontend\src\components\dashboard",
  "frontend\src\components\evidence", "frontend\src\components\timeline", "frontend\src\components\reports",
  "frontend\src\components\ai", "frontend\src\hooks", "frontend\src\layouts", "frontend\src\routes",
  "frontend\src\services", "frontend\src\store", "frontend\src\styles", "frontend\src\types", "frontend\src\utils",
  "frontend\src\pages\Login", "frontend\src\pages\Dashboard", "frontend\src\pages\Cases",
  "frontend\src\pages\Evidence", "frontend\src\pages\Timeline", "frontend\src\pages\Alerts",
  "frontend\src\pages\Reports", "frontend\src\pages\AIAssistant", "frontend\src\pages\Settings",
  "backend\app\api", "backend\app\core", "backend\app\database\migrations",
  "backend\app\middleware", "backend\app\models", "backend\app\schemas", "backend\app\services",
  "backend\app\parsers\evtx", "backend\app\parsers\csv", "backend\app\parsers\json",
  "backend\app\parsers\xml", "backend\app\parsers\linux_logs",
  "backend\app\correlation", "backend\app\timeline", "backend\app\detection",
  "backend\app\reports", "backend\app\ai", "backend\app\utils",
  "backend\uploads", "backend\logs", "backend\tests",
  "datasets\sample_logs", "datasets\evtx", "datasets\csv", "datasets\json", "datasets\xml",
  "datasets\linux", "datasets\test_cases",
  "database\migrations", "database\backups",
  "ai\prompts", "ai\embeddings", "ai\vector_db", "ai\models", "ai\context_builder", "ai\report_templates",
  "reports\generated", "reports\templates", "reports\exports",
  "scripts",
  "docker",
  ".github\workflows",
  "tests\frontend", "tests\backend", "tests\integration", "tests\performance"
)
foreach ($d in $dirs) {
  New-Item -ItemType Directory -Force -Path $d | Out-Null
}
Write-Host "All directories created successfully!"
