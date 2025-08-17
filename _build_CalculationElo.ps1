$PythonExe = "C:\Python27\python.exe"
$PackerUser = "me.under_pressure"
$PackerName = "calculationelo"
$PackerVersion = "0.0.6"
$PackerDescription = "Shows various information about the opponent in the stronghold battles."


$BaseDir = $PSScriptRoot
$ScriptPath = Join-Path $BaseDir "compile_all.py"
$SourceDir = Join-Path $BaseDir "source"
$DestDir = Join-Path $BaseDir "res\scripts\client\gui\mods"
$ResDir = Join-Path $BaseDir "res"



if (-not (Test-Path $PythonExe)) {
    Write-Host "Error: Python not found at $PythonExe" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ScriptPath)) {
    Write-Host "Error: compile_all.py not found at $ScriptPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $DestDir)) {
    Write-Host "Creating destination directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
}

Write-Host "Starting compilation..." -ForegroundColor Green
try {
    Set-Location (Split-Path $ScriptPath)
    
    & $PythonExe compile_all.py -f -d $DestDir $SourceDir
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Compilation completed successfully!" -ForegroundColor Green
        
        Write-Host "Moving .pyc files to destination..." -ForegroundColor Yellow
        Get-ChildItem -Path $SourceDir -Filter "*.pyc" -Recurse | ForEach-Object {
            $relativePath = $_.FullName.Substring($SourceDir.Length)
            $targetPath = Join-Path $DestDir $relativePath
            $targetDir = Split-Path $targetPath -Parent
            
            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }
            
            Move-Item $_.FullName $targetPath -Force
            Write-Host "Moved: $($_.Name)" -ForegroundColor Green
        }
        
        Write-Host "`nStarting packer.py..." -ForegroundColor Green
        Set-Location -Path './'
        & $PythonExe 'packer.py' -u $PackerUser -n $PackerName -v $PackerVersion -d $PackerDescription -f 'res'
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Packer.py completed successfully!" -ForegroundColor Green
        } else {
            Write-Host "Error during packing. Exit code: $LASTEXITCODE" -ForegroundColor Red
        }
    } else {
        Write-Host "Error during compilation. Exit code: $LASTEXITCODE" -ForegroundColor Red
    }
}
catch {
    Write-Host "An error occurred: $_" -ForegroundColor Red
}

Write-Host "`nScript execution completed!" -ForegroundColor Green
Write-Host "Compiled files are in: $DestDir" -ForegroundColor Yellow

Write-Host "`nCleaning up res directory..." -ForegroundColor Yellow
try {
    if (Test-Path $ResDir) {
        Remove-Item -Path $ResDir -Recurse -Force
        Write-Host "Successfully deleted res directory and its contents!" -ForegroundColor Green
    } else {
        Write-Host "Res directory not found - nothing to clean up." -ForegroundColor Yellow
    }
}
catch {
    Write-Host "Error deleting res directory: $_" -ForegroundColor Red
}

Write-Host "`nPress any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
