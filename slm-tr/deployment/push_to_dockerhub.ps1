# PowerShell Utility: Tag & Push SLM Trainer Images to Docker Hub

Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "          🐳  SLM DOCKER HUB DEPLOYMENT HELPER (WINDOWS) 🐳          " -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan

# 1. Ask for Docker Hub Username
$dockerHubUser = Read-Host "[*] Enter your Docker Hub Username"
if ([string]::IsNullOrWhiteSpace($dockerHubUser)) {
    Write-Host "[!] Username cannot be empty. Exiting." -ForegroundColor Red
    Exit
}

# 2. Select image variant
Write-Host "`nSelect the image variant you want to push:" -ForegroundColor Green
Write-Host "  1) GPU Accelerated Image (slm-trainer:gpu)"
Write-Host "  2) CPU Standard Image (slm-trainer:cpu)"
Write-Host "  3) Both Variants"
$variantChoice = Read-Host "[*] Choice (1-3)"

# 3. Prompt for Login verification
Write-Host "`n[!] IMPORTANT: Ensure you have executed 'docker login' in your shell beforehand." -ForegroundColor Yellow
$loginConfirm = Read-Host "[*] Are you logged into Docker Hub? (y/n)"
if ($loginConfirm -ne "y" -and $loginConfirm -ne "yes") {
    Write-Host "[*] Please execute 'docker login' in your command prompt or terminal first, then run this script." -ForegroundColor Red
    Exit
}

# 4. Perform tagging and pushing
if ($variantChoice -eq "1" -or $variantChoice -eq "3") {
    Write-Host "`n[*] Tagging GPU image..." -ForegroundColor Green
    docker tag slm-trainer:gpu "${dockerHubUser}/slm-trainer:gpu"
    
    Write-Host "[*] Pushing GPU image to Docker Hub..." -ForegroundColor Green
    docker push "${dockerHubUser}/slm-trainer:gpu"
    
    Write-Host "[✓] GPU image successfully pushed to: https://hub.docker.com/r/${dockerHubUser}/slm-trainer" -ForegroundColor Green
}

if ($variantChoice -eq "2" -or $variantChoice -eq "3") {
    Write-Host "`n[*] Tagging CPU image..." -ForegroundColor Green
    docker tag slm-trainer:cpu "${dockerHubUser}/slm-trainer:cpu"
    
    Write-Host "[*] Pushing CPU image to Docker Hub..." -ForegroundColor Green
    docker push "${dockerHubUser}/slm-trainer:cpu"
    
    Write-Host "[✓] CPU image successfully pushed to: https://hub.docker.com/r/${dockerHubUser}/slm-trainer" -ForegroundColor Green
}

Write-Host "`n=======================================================================" -ForegroundColor Cyan
Write-Host "🎉 DEPLOYMENT ASSISTANT COMPLETED!" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan
