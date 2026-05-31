# PowerShell Utility: Tag & Push SLM Trainer Image (gpucpu unified tag) to Docker Hub

Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "          🐳  SLM DOCKER HUB DEPLOYMENT HELPER (WINDOWS) 🐳          " -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan

# 1. Ask for Docker Hub Username
$dockerHubUser = Read-Host "[*] Enter your Docker Hub Username"
if ([string]::IsNullOrWhiteSpace($dockerHubUser)) {
    Write-Host "[!] Username cannot be empty. Exiting." -ForegroundColor Red
    Exit
}

# 2. Prompt for Login verification
Write-Host "`n[!] IMPORTANT: Ensure you have executed 'docker login' in your shell beforehand." -ForegroundColor Yellow
$loginConfirm = Read-Host "[*] Are you logged into Docker Hub? (y/n)"
if ($loginConfirm -ne "y" -and $loginConfirm -ne "yes") {
    Write-Host "[*] Please execute 'docker login' in your command prompt or terminal first, then run this script." -ForegroundColor Red
    Exit
}

# 3. Perform tagging and pushing
Write-Host "`n[*] Tagging unified GPU/CPU image..." -ForegroundColor Green
docker tag gauravraval/slm-trainer:gpucpu "${dockerHubUser}/slm-trainer:gpucpu"

Write-Host "[*] Pushing unified GPU/CPU image to Docker Hub..." -ForegroundColor Green
docker push "${dockerHubUser}/slm-trainer:gpucpu"

Write-Host "`n[✓] Image successfully pushed to: https://hub.docker.com/r/${dockerHubUser}/slm-trainer" -ForegroundColor Green
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "🎉 DEPLOYMENT ASSISTANT COMPLETED!" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan
