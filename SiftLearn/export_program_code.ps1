# ============================================================
# SIFT LEARN - PROGRAM CODE EXPORTER
# ============================================================

$Root = (Get-Location).Path

$OutputFile = Join-Path `
    $Root `
    "SIFT_PROGRAM_CODE_REVIEW.txt"


# ------------------------------------------------------------
# Directories to exclude
# ------------------------------------------------------------

$ExcludedDirectories = @(
    ".venv",
    "venv",
    "env",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "build",
    "dist"
)


# ------------------------------------------------------------
# File extensions to include
# ------------------------------------------------------------

$AllowedExtensions = @(
    ".py",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".css",
    ".html"
)


# ------------------------------------------------------------
# Files to exclude
# ------------------------------------------------------------

$ExcludedFileNames = @(
    ".env",
    ".env.local",
    ".env.production",
    "sift.db",
    "database.db",
    "sqlite.db"
)


# ------------------------------------------------------------
# Get all candidate files
# ------------------------------------------------------------

$AllFiles = Get-ChildItem `
    -Path $Root `
    -Recurse `
    -File `
    -ErrorAction SilentlyContinue


$Files = @()


foreach ($File in $AllFiles) {

    # --------------------------------------------------------
    # Extension check
    # --------------------------------------------------------

    if (
        $AllowedExtensions -notcontains `
        $File.Extension.ToLower()
    ) {
        continue
    }


    # --------------------------------------------------------
    # Filename exclusions
    # --------------------------------------------------------

    if (
        $ExcludedFileNames -contains `
        $File.Name.ToLower()
    ) {
        continue
    }


    # --------------------------------------------------------
    # Test-file exclusions
    # --------------------------------------------------------

    $LowerName = $File.Name.ToLower()

    if ($LowerName.StartsWith("test_")) {
        continue
    }

    if ($LowerName.EndsWith("_test.py")) {
        continue
    }

    if ($LowerName -eq "conftest.py") {
        continue
    }


    # --------------------------------------------------------
    # Directory exclusions
    # --------------------------------------------------------

    $RelativePath = $File.FullName.Substring(
        $Root.Length
    ).TrimStart(
        '\',
        '/'
    )

    $PathParts = $RelativePath -split '[\\/]'

    $ShouldExclude = $false

    foreach ($Directory in $ExcludedDirectories) {

        if ($PathParts -contains $Directory) {
            $ShouldExclude = $true
            break
        }
    }

    if ($ShouldExclude) {
        continue
    }


    # --------------------------------------------------------
    # File passed all filters
    # --------------------------------------------------------

    $Files += $File
}


# ------------------------------------------------------------
# Sort files
# ------------------------------------------------------------

$Files = $Files | Sort-Object FullName


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

$Header = @"
======================================================================
SIFT LEARN - COMPLETE PROGRAM CODE REVIEW
======================================================================

Generated:
$(Get-Date)

Project root:
$Root

Files included:
$($Files.Count)

This file contains application source code only.

Excluded:
- test files
- virtual environments
- Git metadata
- Python caches
- node_modules
- build/dist folders
- .env files
- database files
- secrets

======================================================================

"@


Set-Content `
    -Path $OutputFile `
    -Value $Header `
    -Encoding UTF8


# ------------------------------------------------------------
# Export source files
# ------------------------------------------------------------

foreach ($File in $Files) {

    $RelativePath = $File.FullName.Substring(
        $Root.Length
    ).TrimStart(
        '\',
        '/'
    )


    $Separator = @"

======================================================================
FILE: $RelativePath
FULL PATH: $($File.FullName)
SIZE: $($File.Length) bytes
======================================================================

"@


    Add-Content `
        -Path $OutputFile `
        -Value $Separator `
        -Encoding UTF8


    try {

        $Content = Get-Content `
            -Path $File.FullName `
            -Raw `
            -ErrorAction Stop

        Add-Content `
            -Path $OutputFile `
            -Value $Content `
            -Encoding UTF8

    }
    catch {

        Add-Content `
            -Path $OutputFile `
            -Value (
                "[ERROR READING FILE: " +
                $_.Exception.Message +
                "]"
            ) `
            -Encoding UTF8
    }


    Add-Content `
        -Path $OutputFile `
        -Value "`r`n" `
        -Encoding UTF8
}


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

$Footer = @"

======================================================================
END OF SIFT PROGRAM CODE
======================================================================

Total source files exported: $($Files.Count)

Generated file:
$OutputFile

======================================================================
"@


Add-Content `
    -Path $OutputFile `
    -Value $Footer `
    -Encoding UTF8


# ------------------------------------------------------------
# Terminal output
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================"
Write-Host "SIFT PROGRAM EXPORT COMPLETE"
Write-Host "============================================================"
Write-Host ""

Write-Host "Files exported: $($Files.Count)"

Write-Host ""

Write-Host "Output file:"
Write-Host $OutputFile

Write-Host ""

Write-Host "Excluded:"
Write-Host "  - test files"
Write-Host "  - .venv"
Write-Host "  - .git"
Write-Host "  - __pycache__"
Write-Host "  - .env"
Write-Host "  - database files"

Write-Host ""
Write-Host "============================================================"