#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Monitor GPU training progress in real-time
.DESCRIPTION
    Displays training log output and GPU utilization
#>

param(
    [int]$RefreshSeconds = 10
)

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     🔥 GPU Training Monitor - AgriSense 🔥                   ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$logPattern = "gpu_training_*.log"

while ($true) {
    Clear-Host
    
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "🔥 GPU Training Progress Monitor" -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "Refresh Time: $(Get-Date -Format 'HH:mm:ss')`n" -ForegroundColor Gray
    
    # Check if training process is running
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*\.venv\*" }
    
    if ($pythonProcesses) {
        Write-Host "✅ Training Process: RUNNING" -ForegroundColor Green
        Write-Host "   Process ID(s): $($pythonProcesses.Id -join ', ')" -ForegroundColor Gray
        Write-Host "   Memory Usage: $([math]::Round($pythonProcesses[0].WorkingSet64 / 1MB, 2)) MB`n" -ForegroundColor Gray
    } else {
        Write-Host "❌ Training Process: NOT RUNNING`n" -ForegroundColor Red
    }
    
    # GPU Status
    Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host "🎮 GPU Status" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    
    try {
        $gpuInfo = nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv,noheader 2>$null
        
        if ($gpuInfo) {
            $parts = $gpuInfo -split ','
            Write-Host "GPU: $($parts[0].Trim())" -ForegroundColor Cyan
            Write-Host "Temperature: $($parts[1].Trim())°C" -ForegroundColor $(if ([int]$parts[1].Trim() -gt 70) { "Red" } else { "Green" })
            Write-Host "GPU Utilization: $($parts[2].Trim())" -ForegroundColor Yellow
            Write-Host "Memory Utilization: $($parts[3].Trim())" -ForegroundColor Yellow
            Write-Host "VRAM Used: $($parts[4].Trim()) / $($parts[5].Trim())`n" -ForegroundColor Magenta
        } else {
            Write-Host "⚠️  Unable to query GPU (nvidia-smi not available)`n" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Unable to query GPU`n" -ForegroundColor Yellow
    }
    
    # Latest Training Log
    Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    Write-Host "📊 Training Log (Last 25 lines)" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
    
    $logFile = Get-ChildItem -Path "." -Filter $logPattern -ErrorAction SilentlyContinue | 
               Sort-Object LastWriteTime -Descending | 
               Select-Object -First 1
    
    if ($logFile) {
        $lastLines = Get-Content $logFile.FullName -Tail 25 -ErrorAction SilentlyContinue
        
        foreach ($line in $lastLines) {
            # Color-code log levels
            if ($line -match "ERROR") {
                Write-Host $line -ForegroundColor Red
            } elseif ($line -match "WARNING") {
                Write-Host $line -ForegroundColor Yellow
            } elseif ($line -match "Epoch.*Accuracy") {
                Write-Host $line -ForegroundColor Green
            } elseif ($line -match "Training.*model|Best.*Model") {
                Write-Host $line -ForegroundColor Cyan
            } elseif ($line -match "✅|🏆|🎉") {
                Write-Host $line -ForegroundColor Green
            } else {
                Write-Host $line
            }
        }
        
        Write-Host "`nLog file: $($logFile.Name)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  No training log file found`n" -ForegroundColor Yellow
    }
    
    Write-Host "`n═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to exit. Refreshing in $RefreshSeconds seconds..." -ForegroundColor Gray
    
    Start-Sleep -Seconds $RefreshSeconds
}
