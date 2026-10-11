param(
    [switch]$SkipComposeUp
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker CLI was not found. Install and start Docker Desktop first.'
}

if (-not (Test-Path -LiteralPath '.env')) {
    if (-not (Test-Path -LiteralPath '.env.example')) {
        throw 'Neither .env nor .env.example exists.'
    }
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
    Write-Host 'Created .env from .env.example. The default values are for local coursework use.' -ForegroundColor Yellow
}

docker compose config --quiet
if ($LASTEXITCODE -ne 0) {
    throw 'docker compose configuration validation failed.'
}

if (-not $SkipComposeUp) {
    Write-Host 'Starting database containers and refreshing mounted SQL files...'
    docker compose up -d --wait
    if ($LASTEXITCODE -ne 0) {
        throw 'docker compose up failed. Confirm that Docker Desktop is running and database ports are available.'
    }
}

$targets = @(
    @{ Service = 'coordinator-db'; Schema = '/docker-entrypoint-initdb.d/010_schema.sql'; Seed = '/docker-entrypoint-initdb.d/020_seed.sql' },
    @{ Service = 'site1-db'; Schema = '/docker-entrypoint-initdb.d/010_schema.sql'; Seed = '/docker-entrypoint-initdb.d/020_seed.sql' },
    @{ Service = 'site2-db'; Schema = '/docker-entrypoint-initdb.d/010_schema.sql'; Seed = '/docker-entrypoint-initdb.d/020_seed.sql' },
    @{ Service = 'site3-db'; Schema = '/docker-entrypoint-initdb.d/010_schema.sql'; Seed = '/docker-entrypoint-initdb.d/020_seed.sql' }
)

foreach ($target in $targets) {
    Write-Host ("Applying extensions, schema and demo data to {0}..." -f $target.Service)

    $scripts = @(
        '/docker-entrypoint-initdb.d/001_extensions.sql',
        $target.Schema,
        $target.Seed
    )

    foreach ($sqlFile in $scripts) {
        $psqlCommand = 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "{0}"' -f $sqlFile
        docker compose exec -T $target.Service sh -lc $psqlCommand

        if ($LASTEXITCODE -ne 0) {
            throw ("SQL import failed for {0}: {1}" -f $target.Service, $sqlFile)
        }
    }
}

Write-Host 'All database schemas and demo data were applied successfully.' -ForegroundColor Green
