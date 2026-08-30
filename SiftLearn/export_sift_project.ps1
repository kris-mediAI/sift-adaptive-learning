# ============================================================
# SIFTLEARN - CODE ONLY EXPORT
# ============================================================

$root = (Get-Location).Path
$output = Join-Path $root "SIFT_CODE_ONLY.txt"

# Remove old export
Remove-Item $output -ErrorAction SilentlyContinue

# ============================================================
# EXCLUDED DIRECTORIES
# ============================================================

$excludedDirectories = @(
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "build",
    "dist"
)

# ============================================================
# CHECK IF PATH IS EXCLUDED
# ============================================================

function Is-Excluded {
    param(
        [string]$Path
    )

    foreach ($directory in $excludedDirectories) {

        $pattern = [regex]::Escape(
            "\" + $directory + "\"
        )

        if ($Path -match $pattern) {
            return $true
        }

        if ($Path.EndsWith(
            "\" + $directory
        )) {
            return $true
        }
    }

    return $false
}

# ============================================================
# GET PYTHON FILES
# ============================================================

$pythonFiles = Get-ChildItem `
    -Path $root `
    -Recurse `
    -File `
    -Filter "*.py" `
    -Force |
    Where-Object {
        -not (Is-Excluded $_.FullName)
    }

# ============================================================
# ORDER FILES
# ============================================================

function Get-Order {
    param(
        [string]$Path
    )

    $relative = $Path.Substring(
        $root.Length
    ).TrimStart("\", "/")

    # --------------------------------------------------------
    # AI
    # --------------------------------------------------------

    if ($relative -match "^ai\\") {
        return 10
    }

    # --------------------------------------------------------
    # CORE MODELS / DOMAIN
    # --------------------------------------------------------

    if ($relative -match "^core\\.*model") {
        return 20
    }

    if ($relative -match "^core\\learner") {
        return 21
    }

    if ($relative -match "^core\\concept") {
        return 22
    }

    if ($relative -match "^core\\knowledge") {
        return 23
    }

    if ($relative -match "^core\\subject") {
        return 24
    }

    # --------------------------------------------------------
    # CORE ENGINES
    # --------------------------------------------------------

    if ($relative -match "^core\\adaptive") {
        return 30
    }

    if ($relative -match "^core\\strategy") {
        return 31
    }

    if ($relative -match "^core\\task") {
        return 32
    }

    if ($relative -match "^core\\content") {
        return 33
    }

    # --------------------------------------------------------
    # CORE SESSION / ORCHESTRATION
    # --------------------------------------------------------

    if ($relative -match "^core\\session") {
        return 40
    }

    if ($relative -match "^core\\orchestrator") {
        return 41
    }

    if ($relative -match "^core\\time") {
        return 42
    }

    if ($relative -match "^core\\repository") {
        return 43
    }

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    if ($relative -match "^database\\") {
        return 50
    }

    # --------------------------------------------------------
    # TESTS
    # --------------------------------------------------------

    if (
        $relative -match "^tests\\" -or
        $relative -match "\\test_.*\.py$" -or
        $relative -match "^test_.*\.py$"
    ) {
        return 90
    }

    # --------------------------------------------------------
    # ROOT FILES
    # --------------------------------------------------------

    if (
        $relative -notmatch "\\"
    ) {
        return 100
    }

    # --------------------------------------------------------
    # EVERYTHING ELSE
    # --------------------------------------------------------

    return 80
}

$orderedFiles = $pythonFiles |
    Sort-Object `
        @{ Expression = {
            Get-Order $_.FullName
        }},
        @{ Expression = {
            $_.FullName
        }}

# ============================================================
# HEADER
# ============================================================

"============================================================" |
    Out-File $output -Encoding utf8

"SIFTLEARN CODE SNAPSHOT" |
    Out-File $output -Append -Encoding utf8

"============================================================" |
    Out-File $output -Append -Encoding utf8

"PROJECT ROOT:" |
    Out-File $output -Append -Encoding utf8

$root |
    Out-File $output -Append -Encoding utf8

"" |
    Out-File $output -Append -Encoding utf8

"PYTHON FILES: $($orderedFiles.Count)" |
    Out-File $output -Append -Encoding utf8

"" |
    Out-File $output -Append -Encoding utf8

# ============================================================
# WRITE FILES
# ============================================================

$number = 1

foreach ($file in $orderedFiles) {

    $relative = $file.FullName.Substring(
        $root.Length
    ).TrimStart(
        "\",
        "/"
    )

    "" |
        Out-File $output -Append -Encoding utf8

    "============================================================" |
        Out-File $output -Append -Encoding utf8

    "FILE $number" |
        Out-File $output -Append -Encoding utf8

    "PATH: $relative" |
        Out-File $output -Append -Encoding utf8

    "============================================================" |
        Out-File $output -Append -Encoding utf8

    try {

        $content = Get-Content `
            -LiteralPath $file.FullName `
            -Raw `
            -ErrorAction Stop

        $content |
            Out-File $output -Append -Encoding utf8
    }
    catch {

        "[ERROR READING FILE]" |
            Out-File $output -Append -Encoding utf8

        $_.Exception.Message |
            Out-File $output -Append -Encoding utf8
    }

    $number++
}

# ============================================================
# END
# ============================================================

"" |
    Out-File $output -Append -Encoding utf8

"============================================================" |
    Out-File $output -Append -Encoding utf8

"END OF SIFTLEARN CODE SNAPSHOT" |
    Out-File $output -Append -Encoding utf8

"============================================================" |
    Out-File $output -Append -Encoding utf8

Write-Host ""
Write-Host "============================================================"
Write-Host "SIFT CODE EXPORT COMPLETE"
Write-Host "============================================================"
Write-Host ""
Write-Host "Python files exported: $($orderedFiles.Count)"
Write-Host ""
Write-Host "Output:"
Write-Host $output
Write-Host ""