<#
PowerShell helper: print proposed git mv commands for a safe reorganization.
This script only prints commands — it does not modify files.
Run: pwsh ./scripts/propose_reorg.ps1
#>

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root

$csvs = @(
    'sikkim_crop_dataset.csv',
    'data_core.csv',
    'merged_chatbot_training_dataset.csv',
    'weather_cache.csv',
    'Farming_FAQ_Assistant_Dataset.csv',
    'Farming_FAQ_Assistant_Dataset (2).csv'
)

Write-Host "Proposed moves (preview only). Review before running."
Write-Host "Create directories: data and models"
Write-Host "mkdir data; mkdir models"
Write-Host "----\nMove dataset CSVs to data/ (git mv preserves history)"

foreach ($f in $csvs) {
    if (Test-Path $f) {
        Write-Host "git mv `"$f`" data/"
    }
    else {
        Write-Host "# skip (not found): $f"
    }
}

Write-Host "----\nMove small model artifacts into agrisense_app/backend/models/ when safe. Example:"
Write-Host "mkdir -p agrisense_app/backend/models"
Write-Host "git mv best_crop_tf.keras agrisense_app/backend/models/  # verify size before moving"

Write-Host "----\nCreate high-level data/README.md and models/README.md and commit the changes."
Write-Host "After reviewing, you can run the printed git mv commands or copy them into a script to execute."

Write-Host "Done. This script is a preview helper only."
