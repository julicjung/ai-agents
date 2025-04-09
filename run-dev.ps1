# Set working directory to project root (where this script is located)
Set-Location $PSScriptRoot

# Add src directory to PYTHONPATH when running from workspace root
$env:PYTHONPATH = Join-Path $PSScriptRoot "src"

# Run uvicorn from project root, but specify the module path using --app-dir
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --app-dir src