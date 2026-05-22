#!/bin/bash
# Bash Utility: Tag & Push SLM Trainer Images to Docker Hub

# Color declarations
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}=======================================================================${NC}"
echo -e "${CYAN}          🐳  SLM DOCKER HUB DEPLOYMENT HELPER (LINUX) 🐳          ${NC}"
echo -e "${CYAN}=======================================================================${NC}"

# 1. Ask for Docker Hub Username
read -p "Enter your Docker Hub Username: " dockerHubUser
if [ -z "$dockerHubUser" ]; then
    echo -e "${RED}[!] Username cannot be empty. Exiting.${NC}"
    exit 1
fi

# 2. Select image variant
echo -e "\n${GREEN}Select the image variant you want to push:${NC}"
echo "  1) GPU Accelerated Image (slm-trainer:gpu)"
echo "  2) CPU Standard Image (slm-trainer:cpu)"
echo "  3) Both Variants"
read -p "Choice (1-3): " variantChoice

# 3. Prompt for Login verification
echo -e "\n${YELLOW}[!] IMPORTANT: Ensure you have executed 'docker login' in your shell beforehand.${NC}"
read -p "Are you logged into Docker Hub? (y/n): " loginConfirm
if [ "$loginConfirm" != "y" ] && [ "$loginConfirm" != "yes" ]; then
    echo -e "${RED}[*] Please execute 'docker login' first, then run this script.${NC}"
    exit 1
fi

# 4. Perform tagging and pushing
if [ "$variantChoice" = "1" ] || [ "$variantChoice" = "3" ]; then
    echo -e "\n${GREEN}[*] Tagging GPU image...${NC}"
    docker tag slm-trainer:gpu "${dockerHubUser}/slm-trainer:gpu"
    
    echo -e "${GREEN}[*] Pushing GPU image to Docker Hub...${NC}"
    docker push "${dockerHubUser}/slm-trainer:gpu"
    
    echo -e "${GREEN}[✓] GPU image successfully pushed to: https://hub.docker.com/r/${dockerHubUser}/slm-trainer${NC}"
fi

if [ "$variantChoice" = "2" ] || [ "$variantChoice" = "3" ]; then
    echo -e "\n${GREEN}[*] Tagging CPU image...${NC}"
    docker tag slm-trainer:cpu "${dockerHubUser}/slm-trainer:cpu"
    
    echo -e "${GREEN}[*] Pushing CPU image to Docker Hub...${NC}"
    docker push "${dockerHubUser}/slm-trainer:cpu"
    
    echo -e "${GREEN}[✓] CPU image successfully pushed to: https://hub.docker.com/r/${dockerHubUser}/slm-trainer${NC}"
fi

echo -e "${CYAN}=======================================================================${NC}"
echo -e "${CYAN}🎉 DEPLOYMENT ASSISTANT COMPLETED!${NC}"
echo -e "${CYAN}=======================================================================${NC}"
