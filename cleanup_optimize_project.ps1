# AgriSense Project Cleanup & Optimization Script
# Run from: AGRISENSEFULL-STACK directory
# Purpose: Clean cache, organize files, optimize project structure

param(
    [switch]$DryRun = $false,
    [switch]$SkipBackup = $false
)

$ErrorActionPreference = "Continue"

Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🧹 AgriSense Project Cleanup & Optimization 🧹        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "agrisense_app")) {
    Write-Host "❌ Error: Must run from AGRISENSEFULL-STACK directory" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# Backup option
if (-not $SkipBackup -and -not $DryRun) {
    Write-Host "`n📦 Creating backup (optional)..." -ForegroundColor Yellow
    $createBackup = Read-Host "Create backup before cleanup? (y/N)"
    if ($createBackup -eq 'y' -or $createBackup -eq 'Y') {
        $date = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupPath = "..\AGRISENSEFULL-STACK_backup_$date"
        Write-Host "Creating backup at: $backupPath" -ForegroundColor Cyan
        Copy-Item -Path "." -Destination $backupPath -Recurse -Force -Exclude ".venv",".venv-ml",".venv-tf","__pycache__",".pytest_cache","node_modules"
        Write-Host "✅ Backup created" -ForegroundColor Green
    }
}

if ($DryRun) {
    Write-Host "`n🔍 DRY RUN MODE - No files will be modified`n" -ForegroundColor Magenta
}

# Statistics
$stats = @{
    CacheFilesDeleted = 0
    ScriptsMoved = 0
    TestsMoved = 0
    DocsMoved = 0
    OldReportsArchived = 0
    ConfigsMoved = 0
    DataFilesMoved = 0
}

# ============================================================================
# Phase 1: Delete Cache & Temporary Files
# ============================================================================
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📦 Phase 1: Cleaning cache and temporary files..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Count cache files first
$pycacheCount = (Get-ChildItem -Path . -Include __pycache__ -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count
$pytestCacheCount = (Get-ChildItem -Path . -Include .pytest_cache -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count
$pycCount = (Get-ChildItem -Path . -Filter "*.pyc" -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count

Write-Host "  Found:" -ForegroundColor White
Write-Host "    - $pycacheCount __pycache__ directories" -ForegroundColor Gray
Write-Host "    - $pytestCacheCount .pytest_cache directories" -ForegroundColor Gray
Write-Host "    - $pycCount .pyc files" -ForegroundColor Gray

if (-not $DryRun) {
    # Delete Python cache
    Get-ChildItem -Path . -Include __pycache__ -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    Get-ChildItem -Path . -Include .pytest_cache -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    Get-ChildItem -Path . -Filter "*.pyc" -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Force
    
    # Delete old virtual environments (skip if in use)
    if (Test-Path ".venv-ml") {
        try {
            Remove-Item -Path ".venv-ml" -Recurse -Force -ErrorAction Stop
            Write-Host "  🗑️  Deleted .venv-ml/" -ForegroundColor Red
        } catch {
            Write-Host "  ⚠️  Could not delete .venv-ml/ (may be in use)" -ForegroundColor Yellow
        }
    }
    if (Test-Path ".venv-tf") {
        try {
            Remove-Item -Path ".venv-tf" -Recurse -Force -ErrorAction Stop
            Write-Host "  🗑️  Deleted .venv-tf/" -ForegroundColor Red
        } catch {
            Write-Host "  ⚠️  Could not delete .venv-tf/ (may be in use)" -ForegroundColor Yellow
        }
    }
    
    $stats.CacheFilesDeleted = $pycacheCount + $pytestCacheCount + $pycCount
    Write-Host "  ✅ Deleted $($stats.CacheFilesDeleted) cache files/directories" -ForegroundColor Green
} else {
    Write-Host "  [DRY RUN] Would delete $($pycacheCount + $pytestCacheCount + $pycCount) items" -ForegroundColor Magenta
}

# ============================================================================
# Phase 2: Organize Test Files
# ============================================================================
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📝 Phase 2: Organizing test files..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

$testFiles = Get-ChildItem -Filter "test_*.py" -File | Where-Object { $_.Name -ne "conftest.py" }
Write-Host "  Found $($testFiles.Count) test files in root" -ForegroundColor White

if ($testFiles.Count -gt 0) {
    if (-not $DryRun) {
        New-Item -Path "tests/legacy" -ItemType Directory -Force | Out-Null
        foreach ($file in $testFiles) {
            Move-Item -Path $file.FullName -Destination "tests/legacy/" -Force
            Write-Host "  📁 $($file.Name) → tests/legacy/" -ForegroundColor Cyan
            $stats.TestsMoved++
        }
        Write-Host "  ✅ Moved $($stats.TestsMoved) test files" -ForegroundColor Green
    } else {
        foreach ($file in $testFiles) {
            Write-Host "  [DRY RUN] Would move: $($file.Name) → tests/legacy/" -ForegroundColor Magenta
        }
    }
}

# ============================================================================
# Phase 3: Organize Scripts
# ============================================================================
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🔧 Phase 3: Organizing scripts..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

if (-not $DryRun) {
    New-Item -Path "scripts/debug" -ItemType Directory -Force | Out-Null
    New-Item -Path "scripts/setup" -ItemType Directory -Force | Out-Null
    New-Item -Path "scripts/testing" -ItemType Directory -Force | Out-Null
    New-Item -Path "scripts/archived" -ItemType Directory -Force | Out-Null
}

# Debug scripts
$debugScripts = Get-ChildItem -File | Where-Object { $_.Name -match "^(debug_|check_|analyze_)" }
Write-Host "  Debug scripts: $($debugScripts.Count)" -ForegroundColor White
foreach ($file in $debugScripts) {
    if (-not $DryRun) {
        Move-Item -Path $file.FullName -Destination "scripts/debug/" -Force -ErrorAction SilentlyContinue
        Write-Host "  📁 $($file.Name) → scripts/debug/" -ForegroundColor Cyan
        $stats.ScriptsMoved++
    } else {
        Write-Host "  [DRY RUN] Would move: $($file.Name) → scripts/debug/" -ForegroundColor Magenta
    }
}

# Setup scripts
$setupScripts = Get-ChildItem -Filter "add_crop_*.py" -File
Write-Host "  Setup scripts: $($setupScripts.Count)" -ForegroundColor White
foreach ($file in $setupScripts) {
    if (-not $DryRun) {
        Move-Item -Path $file.FullName -Destination "scripts/setup/" -Force -ErrorAction SilentlyContinue
        Write-Host "  📁 $($file.Name) → scripts/setup/" -ForegroundColor Cyan
        $stats.ScriptsMoved++
    } else {
        Write-Host "  [DRY RUN] Would move: $($file.Name) → scripts/setup/" -ForegroundColor Magenta
    }
}

# Testing scripts
$testingScripts = @("accuracy_test.py", "simple_accuracy_test.py", "comprehensive_e2e_test.py", "run_e2e_tests.py")
foreach ($scriptName in $testingScripts) {
    if (Test-Path $scriptName) {
        if (-not $DryRun) {
            Move-Item -Path $scriptName -Destination "scripts/testing/" -Force
            Write-Host "  📁 $scriptName → scripts/testing/" -ForegroundColor Cyan
            $stats.ScriptsMoved++
        } else {
            Write-Host "  [DRY RUN] Would move: $scriptName → scripts/testing/" -ForegroundColor Magenta
        }
    }
}

# Archive cleanup scripts
$cleanupScripts = Get-ChildItem -Filter "cleanup_*.py" -File
foreach ($file in $cleanupScripts) {
    if (-not $DryRun) {
        Move-Item -Path $file.FullName -Destination "scripts/archived/" -Force -ErrorAction SilentlyContinue
        Write-Host "  📁 $($file.Name) → scripts/archived/" -ForegroundColor Cyan
        $stats.ScriptsMoved++
    } else {
        Write-Host "  [DRY RUN] Would move: $($file.Name) → scripts/archived/" -ForegroundColor Magenta
    }
}

if (-not $DryRun) {
    Write-Host "  ✅ Organized $($stats.ScriptsMoved) scripts" -ForegroundColor Green
}

# ============================================================================
# Phase 4: Archive Old Test Results
# ============================================================================
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📊 Phase 4: Archiving old test results..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

if (-not $DryRun) {
    New-Item -Path "tests/archived_results" -ItemType Directory -Force | Out-Null
}

$testResults = Get-ChildItem -File | Where-Object { $_.Name -match "(test_report|_results|_test.*\.json|e2e_test_results)" }
Write-Host "  Found $($testResults.Count) old test result files" -ForegroundColor White

foreach ($file in $testResults) {
    if (-not $DryRun) {
        Move-Item -Path $file.FullName -Destination "tests/archived_results/" -Force -ErrorAction SilentlyContinue
        Write-Host "  📁 $($file.Name) → tests/archived_results/" -ForegroundColor Cyan
        $stats.OldReportsArchived++
    } else {
        Write-Host "  [DRY RUN] Would move: $($file.Name) → tests/archived_results/" -ForegroundColor Magenta
    }
}

if (-not $DryRun -and $stats.OldReportsArchived -gt 0) {
    Write-Host "  ✅ Archived $($stats.OldReportsArchived) test result files" -ForegroundColor Green
}

# ============================================================================
# Phase 5: Organize Documentation
# ============================================================================
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📚 Phase 5: Organizing documentation..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

if (-not $DryRun) {
    New-Item -Path "documentation/reports" -ItemType Directory -Force | Out-Null
}

$reports = @(
    "COMPLETE_ENHANCEMENT_REPORT_OCT14_2025.md",
    "COMPREHENSIVE_TEST_RESULTS_SUMMARY.md",
    "CRITICAL_FIXES_ACTION_PLAN.md",
    "PRIORITY_FIXES_IMPLEMENTATION.md",
    "PROJECT_EVALUATION_REPORT.md",
    "PROJECT_OPTIMIZATION_FINAL_REPORT.md",
    "SECURITY_UPGRADE_SUMMARY.md",
    "STABILIZATION_COMPLETION_REPORT.md",
    "TROUBLESHOOTING_SUMMARY.md"
)

foreach ($report in $reports) {
    if (Test-Path $report) {
        if (-not $DryRun) {
            Move-Item -Path $report -Destination "documentation/reports/" -Force
            Write-Host "  📁 $report → documentation/reports/" -ForegroundColor Cyan
            $stats.DocsMoved++
        } else {
            Write-Host "  [DRY RUN] Would move: $report → documentation/reports/" -ForegroundColor Magenta
        }
    }
}

if (-not $DryRun -and $stats.DocsMoved -gt 0) {
    Write-Host "  ✅ Moved $($stats.DocsMoved) documentation files" -ForegroundColor Green
}

# ============================================================================
# Phase 6: Organize Data Files
# ============================================================================
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📁 Phase 6: Organizing data files..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

if (Test-Path "48_crops_chatbot.csv") {
    if (-not $DryRun) {
        Move-Item -Path "48_crops_chatbot.csv" -Destination "training_data/" -Force
        Write-Host "  📁 48_crops_chatbot.csv → training_data/" -ForegroundColor Cyan
        $stats.DataFilesMoved++
        Write-Host "  ✅ Moved $($stats.DataFilesMoved) data file(s)" -ForegroundColor Green
    } else {
        Write-Host "  [DRY RUN] Would move: 48_crops_chatbot.csv → training_data/" -ForegroundColor Magenta
    }
}

# ============================================================================
# Phase 7: Organize Config Files
# ============================================================================
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "⚙️  Phase 7: Organizing config files..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

if (Test-Path "arduino.json") {
    if (-not $DryRun) {
        Move-Item -Path "arduino.json" -Destination "config/" -Force
        Write-Host "  📁 arduino.json → config/" -ForegroundColor Cyan
        $stats.ConfigsMoved++
        Write-Host "  ✅ Moved $($stats.ConfigsMoved) config file(s)" -ForegroundColor Green
    } else {
        Write-Host "  [DRY RUN] Would move: arduino.json → config/" -ForegroundColor Magenta
    }
}

# ============================================================================
# Summary
# ============================================================================
Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "║                    ✨ Cleanup Complete! ✨                    ║" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n📊 Summary:" -ForegroundColor Cyan
Write-Host "  ✅ Cache files deleted: $($stats.CacheFilesDeleted)" -ForegroundColor White
Write-Host "  ✅ Scripts organized: $($stats.ScriptsMoved)" -ForegroundColor White
Write-Host "  ✅ Test files moved: $($stats.TestsMoved)" -ForegroundColor White
Write-Host "  ✅ Old test results archived: $($stats.OldReportsArchived)" -ForegroundColor White
Write-Host "  ✅ Documentation organized: $($stats.DocsMoved)" -ForegroundColor White
Write-Host "  ✅ Data files moved: $($stats.DataFilesMoved)" -ForegroundColor White
Write-Host "  ✅ Config files moved: $($stats.ConfigsMoved)" -ForegroundColor White

$totalItems = $stats.CacheFilesDeleted + $stats.ScriptsMoved + $stats.TestsMoved + $stats.OldReportsArchived + $stats.DocsMoved + $stats.DataFilesMoved + $stats.ConfigsMoved
Write-Host "`n  🎯 Total items processed: $totalItems" -ForegroundColor Yellow

if (-not $DryRun) {
    Write-Host "`n✨ Project is now clean and organized!" -ForegroundColor Green
    Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Test application: .\start_agrisense.ps1" -ForegroundColor White
    Write-Host "  2. Run tests: pytest -v" -ForegroundColor White
    Write-Host "  3. Review changes: git status" -ForegroundColor White
    Write-Host "  4. Commit changes: git add . && git commit -m 'chore: cleanup and organize project structure'" -ForegroundColor White
} else {
    Write-Host "`n🔍 This was a DRY RUN - no files were modified" -ForegroundColor Magenta
    Write-Host "Run without -DryRun flag to perform actual cleanup" -ForegroundColor Yellow
}

Write-Host ""
