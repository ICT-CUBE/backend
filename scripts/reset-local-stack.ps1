param(
    [switch] $Force,
    [switch] $Rebuild
)

$ErrorActionPreference = "Stop"

$BackendRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$WorkspaceRoot = Split-Path $BackendRoot -Parent
$BlockchainRoot = Join-Path $WorkspaceRoot "blockchain-server"
$BackendCompose = Join-Path $BackendRoot "docker-compose.dev.yml"
$BlockchainCompose = Join-Path $BlockchainRoot "docker-compose.yml"
$LocalLogDirectory = Join-Path $BlockchainRoot ".local-logs"

function Assert-RequiredPath {
    param([string] $Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required path not found: $Path"
    }
}

function Invoke-NativeCommand {
    param(
        [string] $Description,
        [scriptblock] $Command
    )

    Write-Host "`n==> $Description" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed (exit code: $LASTEXITCODE)"
    }
}

function Wait-DockerHealth {
    param(
        [string] $ContainerName,
        [int] $TimeoutSeconds = 120
    )

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $Health = docker inspect $ContainerName `
            --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" `
            2>$null
        if ($Health -eq "healthy") {
            return
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $Deadline)

    throw "$ContainerName did not become healthy before timeout. Current state: $Health"
}

function Wait-HttpEndpoint {
    param(
        [string] $Url,
        [int] $TimeoutSeconds = 120
    )

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $Response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 5
            if ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 300) {
                return
            }
        }
        catch {
            # Retry connection failures while the service is starting.
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $Deadline)

    throw "Endpoint did not respond before timeout: $Url"
}

function Stop-LocalHardhatNode {
    $Listeners = Get-NetTCPConnection -State Listen -LocalPort 8545 -ErrorAction SilentlyContinue
    foreach ($ProcessId in @($Listeners | Select-Object -ExpandProperty OwningProcess -Unique)) {
        $Process = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId"
        $CommandLine = [string] $Process.CommandLine
        if (
            $Process.Name -ne "node.exe" -or
            $CommandLine -notlike "*$BlockchainRoot*" -or
            $CommandLine -notmatch "hardhat"
        ) {
            throw "Port 8545 is used by an unknown process. PID=$ProcessId Name=$($Process.Name)"
        }

        Write-Host "Stopping the existing Hardhat node. PID=$ProcessId"
        Stop-Process -Id $ProcessId -Force
    }

    $Deadline = (Get-Date).AddSeconds(15)
    while ((Get-NetTCPConnection -State Listen -LocalPort 8545 -ErrorAction SilentlyContinue)) {
        if ((Get-Date) -ge $Deadline) {
            throw "The existing Hardhat node did not release port 8545."
        }
        Start-Sleep -Milliseconds 500
    }
}

function Start-LocalHardhatNode {
    New-Item -ItemType Directory -Path $LocalLogDirectory -Force | Out-Null
    $StdoutPath = Join-Path $LocalLogDirectory "hardhat.stdout.log"
    $StderrPath = Join-Path $LocalLogDirectory "hardhat.stderr.log"
    $NpmCommand = (Get-Command npm.cmd -ErrorAction Stop).Source

    $Process = Start-Process `
        -FilePath $NpmCommand `
        -ArgumentList @("run", "node", "--workspace=contracts/cube-nft") `
        -WorkingDirectory $BlockchainRoot `
        -RedirectStandardOutput $StdoutPath `
        -RedirectStandardError $StderrPath `
        -WindowStyle Hidden `
        -PassThru

    $Deadline = (Get-Date).AddSeconds(60)
    do {
        if ($Process.HasExited) {
            throw "Hardhat node exited during startup. Log: $StderrPath"
        }

        try {
            $RequestBody = '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
            $Response = Invoke-RestMethod `
                -Uri "http://127.0.0.1:8545" `
                -Method Post `
                -ContentType "application/json" `
                -Body $RequestBody `
                -TimeoutSec 3
            if ($Response.result -eq "0x7a69") {
                Write-Host "Hardhat node started. PID=$($Process.Id)"
                return
            }
        }
        catch {
            # Retry until the JSON-RPC endpoint is ready.
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $Deadline)

    throw "Hardhat JSON-RPC did not start before timeout. Log: $StderrPath"
}

Assert-RequiredPath $BackendCompose
Assert-RequiredPath $BlockchainCompose
Assert-RequiredPath (Join-Path $BlockchainRoot "package.json")
Assert-RequiredPath (Join-Path $BackendRoot "scripts\backfill_mint.py")

if (-not $Force) {
    Write-Host "This command deletes the following local Docker volumes:" -ForegroundColor Yellow
    Write-Host "  - backend_mysql-data"
    Write-Host "  - blockchain-server_mysql-data"
    Write-Host "Both Backend and Blockchain local databases will be reset." -ForegroundColor Yellow
    $Confirmation = Read-Host "Type RESET to continue"
    if ($Confirmation -cne "RESET") {
        Write-Host "Cancelled."
        exit 0
    }
}

Write-Host "`nStarting local stack reset." -ForegroundColor Green

Stop-LocalHardhatNode

Push-Location $BackendRoot
try {
    Invoke-NativeCommand "Remove Backend Compose resources and DB volume" {
        docker compose -f $BackendCompose down -v
    }
}
finally {
    Pop-Location
}

Push-Location $BlockchainRoot
try {
    Invoke-NativeCommand "Remove Blockchain Compose resources and DB volume" {
        docker compose -f $BlockchainCompose down -v
    }

    Invoke-NativeCommand "Start Blockchain MySQL" {
        docker compose -f $BlockchainCompose up -d mysql
    }
    Wait-DockerHealth -ContainerName "blockchain-server-mysql-1"

    if (-not (Test-Path -LiteralPath (Join-Path $BlockchainRoot "node_modules"))) {
        Invoke-NativeCommand "Install Blockchain dependencies" {
            npm ci
        }
    }

    Write-Host "`n==> Run Blockchain DB migrations" -ForegroundColor Cyan
    $env:DATABASE_URL = "mysql://cube_nft:cube_nft@127.0.0.1:3307/cube_nft"
    try {
        npm run migration:run --workspace=server
        if ($LASTEXITCODE -ne 0) {
            throw "Blockchain DB migration failed (exit code: $LASTEXITCODE)"
        }
    }
    finally {
        Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    }

    Write-Host "`n==> Start Hardhat node" -ForegroundColor Cyan
    Start-LocalHardhatNode

    Invoke-NativeCommand "Deploy CubeNFT contract" {
        npm run deploy:localhost --workspace=contracts/cube-nft
    }

    if ($Rebuild) {
        Invoke-NativeCommand "Build and start Blockchain Server" {
            docker compose -f $BlockchainCompose up -d --build server
        }
    }
    else {
        Invoke-NativeCommand "Start Blockchain Server" {
            docker compose -f $BlockchainCompose up -d server
        }
    }
    Wait-DockerHealth -ContainerName "blockchain-server-server-1"
    Wait-HttpEndpoint -Url "http://127.0.0.1:3100/health"
}
finally {
    Pop-Location
}

Push-Location $BackendRoot
try {
    if ($Rebuild) {
        Invoke-NativeCommand "Build and start Backend" {
            docker compose -f $BackendCompose up -d --build
        }
    }
    else {
        Invoke-NativeCommand "Start Backend" {
            docker compose -f $BackendCompose up -d
        }
    }
    Wait-DockerHealth -ContainerName "backend-mysql-1"
    Wait-HttpEndpoint -Url "http://127.0.0.1:8000/health/db" -TimeoutSeconds 180

    Invoke-NativeCommand "Backfill Mint existing cubes" {
        docker compose -f $BackendCompose exec -T api python scripts/backfill_mint.py
    }
}
finally {
    Pop-Location
}

Write-Host "`nLocal stack reset and backfill Mint completed." -ForegroundColor Green
Write-Host "Backend Swagger: http://127.0.0.1:8000/docs"
Write-Host "Blockchain health: http://127.0.0.1:3100/health"
Write-Host "Hardhat logs: $LocalLogDirectory"
