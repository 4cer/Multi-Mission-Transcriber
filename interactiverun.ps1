<#
.SYNOPSIS
    Interactive launcher for SessionTranscriber (mmt.py) with persisted defaults.
.DESCRIPTION
    Prompts for the most common arguments, remembers selected values across runs
    (prompt, output directory, language) and keeps the last 5 output base names
    for easy reference. Uses the project's .venv Python interpreter.
#>

$ErrorActionPreference = 'Stop'
$scriptDir = $PSScriptRoot
$mmtScript  = Join-Path $scriptDir 'mmt.py'
$configFile = Join-Path $scriptDir 'mmt_config.json'
$pythonExe  = Join-Path $scriptDir '.venv\Scripts\python.exe'

# ------------------------------------------------------------
# Helper: parse a command-line style string into arguments,
# handling double-quoted entries that may contain spaces.
# ------------------------------------------------------------
function Parse-QuotedArguments {
    param([string]$InputString)
    $args = @()
    $current = ''
    $inQuotes = $false
    for ($i = 0; $i -lt $InputString.Length; $i++) {
        $c = $InputString[$i]
        if ($c -eq '"') {
            if ($inQuotes) {
                if ($current -ne '') { $args += $current; $current = '' }
                $inQuotes = $false
            } else {
                $inQuotes = $true
                if ($current.Trim() -ne '') { $args += $current.Trim(); $current = '' }
            }
        } elseif ($c -eq ' ' -and !$inQuotes) {
            if ($current.Trim() -ne '') { $args += $current.Trim(); $current = '' }
        } else {
            $current += $c
        }
    }
    if ($current.Trim() -ne '') { $args += $current.Trim() }
    return $args
}

# ------------------------------------------------------------
# Load persisted configuration (JSON)
# ------------------------------------------------------------
$config = @{}
if (Test-Path $configFile) {
    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json -AsHashtable
    } catch {
        Write-Warning "Could not load config, starting fresh."
        $config = @{}
    }
}
# Ensure known keys exist
if (-not $config.ContainsKey('last_base_names')) { $config.last_base_names = @() }

# ------------------------------------------------------------
# 1. Input files (required, multiple)
# ------------------------------------------------------------
do {
    $inputLine = Read-Host "Input audio files (space-separated, wrap paths in double quotes)"
    $inputFiles = Parse-QuotedArguments $inputLine
    if ($inputFiles.Count -eq 0) {
        Write-Host "At least one file is required." -ForegroundColor Yellow
    }
} while ($inputFiles.Count -eq 0)

# ------------------------------------------------------------
# 2. Strategy (enum, default 'non-diarized-aligned')
# ------------------------------------------------------------
$strategyMap = @(
    @{ Name='non-diarized-single';  Short='nds' }
    @{ Name='diarized-single';      Short='ds'  }
    @{ Name='non-diarized-multi';   Short='ndm' }
    @{ Name='non-diarized-aligned'; Short='nda' }
)
$strategyDefault = 'non-diarized-aligned'
Write-Host "`nStrategy choices:"
for ($i=0; $i -lt $strategyMap.Count; $i++) {
    Write-Host "  $($i+1)) $($strategyMap[$i].Name) ($($strategyMap[$i].Short))"
}
Write-Host "  Default: $strategyDefault (just press Enter)"
do {
    $strategyInput = Read-Host "Strategy"
    if ([string]::IsNullOrWhiteSpace($strategyInput)) {
        $strategy = $strategyDefault
        break
    }
    # Try as a number
    $num = 0
    if ([int]::TryParse($strategyInput, [ref]$num) -and $num -ge 1 -and $num -le $strategyMap.Count) {
        $strategy = $strategyMap[$num-1].Name
        break
    }
    # Try as a short or long name
    $match = $strategyMap | Where-Object { $_.Name -eq $strategyInput -or $_.Short -eq $strategyInput }
    if ($match) {
        $strategy = $match.Name
        break
    }
    Write-Host "Invalid choice. Use number, full name (e.g. 'diarized-single') or short ('ds')." -ForegroundColor Red
} while ($true)

# ------------------------------------------------------------
# 3. Prompt type (enum, default 'directory')
# ------------------------------------------------------------
$promptTypeMap = @(
    @{ Name='directory'; Short='dir' }
    @{ Name='string';    Short='str' }
)
$promptTypeDefault = 'directory'
Write-Host "`nPrompt type:"
Write-Host "  1) directory"
Write-Host "  2) string"
Write-Host "  Default: directory"
do {
    $ptInput = Read-Host "Prompt type"
    if ([string]::IsNullOrWhiteSpace($ptInput)) {
        $promptType = $promptTypeDefault
        break
    }
    $num = 0
    if ([int]::TryParse($ptInput, [ref]$num) -and $num -ge 1 -and $num -le 2) {
        $promptType = $promptTypeMap[$num-1].Name
        break
    }
    $match = $promptTypeMap | Where-Object { $_.Name -eq $ptInput -or $_.Short -eq $ptInput }
    if ($match) {
        $promptType = $match.Name
        break
    }
    Write-Host "Invalid. Use 'directory'/'dir' or 'string'/'str'." -ForegroundColor Red
} while ($true)

# ------------------------------------------------------------
# 4. Prompt value (depends on type, default from last run if type matches)
# ------------------------------------------------------------
$savedPromptType = $config['last_prompt_type']
$savedPromptVal  = $config['last_prompt']
if ($savedPromptType -eq $promptType -and $savedPromptVal) {
    $promptDefault = $savedPromptVal
    $promptMsg = "Prompt ($promptType) [default: $promptDefault]"
} else {
    $promptDefault = $null
    $promptMsg = "Prompt ($promptType)"
}
$promptValue = Read-Host $promptMsg
if ([string]::IsNullOrWhiteSpace($promptValue)) {
    $promptValue = $promptDefault   # may be $null
}

# ------------------------------------------------------------
# 5. Output directory (default from last run, otherwise none)
# ------------------------------------------------------------
$savedOutDir = $config['last_output_dir']
$outDirMsg = "Output directory"
if ($savedOutDir) { $outDirMsg += " [default: $savedOutDir]" }
$outputDir = Read-Host $outDirMsg
if ([string]::IsNullOrWhiteSpace($outputDir)) {
    $outputDir = $savedOutDir
}

# ------------------------------------------------------------
# 6. Output types (multi, default: json text dense raw)
# ------------------------------------------------------------
$validOutputTypes = @('json', 'text', 'dense', 'raw')
$outTypesDefaults = @('json', 'text', 'dense', 'raw')
do {
    $otInput = Read-Host "Output types (space-separated) [default: json text dense raw]"
    if ([string]::IsNullOrWhiteSpace($otInput)) {
        $outputTypes = $outTypesDefaults
        break
    }
    $candidates = $otInput -split '\s+' | Where-Object { $_ }
    $invalid = $candidates | Where-Object { $_ -notin $validOutputTypes }
    if ($invalid) {
        Write-Host "Invalid types: $($invalid -join ', '). Allowed: $($validOutputTypes -join ', ')" -ForegroundColor Red
    } else {
        $outputTypes = $candidates
        break
    }
} while ($true)

# ------------------------------------------------------------
# 7. Language (optional, default from last run or none)
# ------------------------------------------------------------
$savedLang = $config['last_language']
$langMsg = "Language code/name (e.g. en, pl, polish, english)"
if ($savedLang) { $langMsg += " [default: $savedLang]" }
$language = Read-Host $langMsg
if ([string]::IsNullOrWhiteSpace($language)) {
    $language = $savedLang
}

# ------------------------------------------------------------
# 8. Output base name (optional, show last 5, no default)
# ------------------------------------------------------------
$lastBaseNames = $config['last_base_names']
if ($lastBaseNames.Count -gt 0) {
    Write-Host "`nLast 5 base names:"
    $lastBaseNames | ForEach-Object { Write-Host "  - $_" }
}
$baseName = Read-Host "Output base name (leave empty to omit)"

# ------------------------------------------------------------
# Build argument list for Python script
# ------------------------------------------------------------
$vargs = @()
# input files
$vargs += '-i'
$vargs += $inputFiles

# strategy (required)
$vargs += '--strategy'
$vargs += $strategy

# prompt (optional, but if provided both type and value must be present)
if ($promptType -and $promptValue) {
    $vargs += '--prompt-type'
    $vargs += $promptType
    $vargs += '--prompt'
    $vargs += $promptValue
}

# output directory (optional – Python default is 'output')
if ($outputDir) {
    $vargs += '--output-directory'
    $vargs += $outputDir
}

# output types (required)
$vargs += '--output-types'
$vargs += $outputTypes

# language (optional)
if ($language) {
    $vargs += '--language'
    $vargs += $language
}

# output base name (optional)
if ($baseName) {
    $vargs += '--output-base-name'
    $vargs += $baseName
}

# ------------------------------------------------------------
# Execute the Python entrypoint
# ------------------------------------------------------------
Write-Host "`nRunning: $pythonExe $mmtScript $($vargs -join ' ')" -ForegroundColor Cyan
& $pythonExe $mmtScript @vargs

# ------------------------------------------------------------
# Save configuration for next run
# ------------------------------------------------------------
# Only save if values were actually provided (empty string means "remove default")
if ($promptType -and $promptValue) {
    $config.last_prompt_type = $promptType
    $config.last_prompt      = $promptValue
} else {
    $config.Remove('last_prompt_type')
    $config.Remove('last_prompt')
}

if ($outputDir) {
    $config.last_output_dir = $outputDir
} else {
    $config.Remove('last_output_dir')
}

if ($language) {
    $config.last_language = $language
} else {
    $config.Remove('last_language')
}

# Update last 5 base names (most recent first)
if ($baseName) {
    $names = [System.Collections.ArrayList]@($config.last_base_names)
    $names.Insert(0, $baseName)
    # remove duplicates keeping order
    $seen = @{}
    $unique = $names | Where-Object { -not $seen.ContainsKey($_) -and ($seen[$_] = $true) }
    $config.last_base_names = @($unique | Select-Object -First 5)
}

try {
    $config | ConvertTo-Json -Depth 5 | Set-Content $configFile -Encoding UTF8
} catch {
    Write-Warning "Failed to save configuration: $_"
}