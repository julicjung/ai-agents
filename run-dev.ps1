# Add src directory to PYTHONPATH when running from workspace root
$env:PYTHONPATH = Join-Path $PSScriptRoot "src"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --app-dir src