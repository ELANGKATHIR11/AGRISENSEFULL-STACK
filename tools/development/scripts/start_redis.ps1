Param()

Write-Output "Starting Redis via docker-compose..."
Push-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
try {
    docker compose -f ..\docker\docker-compose.redis.yml up -d
    docker compose -f ..\docker\docker-compose.redis.yml ps
} finally {
    Pop-Location
}
