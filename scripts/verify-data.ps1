$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

function Invoke-ContainerQuery {
    param(
        [Parameter(Mandatory = $true)][string]$Service,
        [Parameter(Mandatory = $true)][string]$Sql
    )

    $Sql | docker compose exec -T $Service sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
    if ($LASTEXITCODE -ne 0) {
        throw "Verification query failed for $Service."
    }
}

Write-Host 'Coordinator counts:'
Invoke-ContainerQuery -Service 'coordinator-db' -Sql "SELECT (SELECT COUNT(*) FROM site_node) AS sites, (SELECT COUNT(*) FROM university) AS universities, (SELECT COUNT(*) FROM campus) AS campuses, (SELECT COUNT(*) FROM category) AS categories, (SELECT COUNT(*) FROM book_catalog) AS books, (SELECT COUNT(*) FROM user_account) AS accounts;"

$siteTargets = @(
    @{ Service = 'site1-db'; Database = 'site1_db' },
    @{ Service = 'site2-db'; Database = 'site2_db' },
    @{ Service = 'site3-db'; Database = 'site3_db' }
)

foreach ($target in $siteTargets) {
    Write-Host ("{0} counts:" -f $target.Database)
    Invoke-ContainerQuery -Service $target.Service -Sql "SELECT (SELECT COUNT(*) FROM library_fragment) AS libraries, (SELECT COUNT(*) FROM reader_fragment) AS readers, (SELECT COUNT(*) FROM book_copy_fragment) AS copies, (SELECT COUNT(*) FROM borrow_record_fragment) AS borrow_records;"
}

Write-Host 'Cross-university borrow example on Site 1:'
Invoke-ContainerQuery -Service 'site1-db' -Sql "SELECT borrow_id, reader_id, copy_id, copy_owner_site_id, borrow_type, borrow_status FROM borrow_record_fragment WHERE borrow_type = 'CROSS_UNIVERSITY';"

Write-Host 'Cross-campus borrow example on Site 3:'
Invoke-ContainerQuery -Service 'site3-db' -Sql "SELECT borrow_id, reader_id, copy_id, copy_owner_site_id, borrow_type, borrow_status FROM borrow_record_fragment WHERE borrow_type = 'CROSS_CAMPUS';"
