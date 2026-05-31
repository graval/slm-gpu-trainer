#!/bin/bash
# Bash Utility: Tag & Push SLM Trainer Image (gpucpu unified tag) to Docker Hub

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

# 2. Prompt for Login verification
echo -e "\n${YELLOW}[!] IMPORTANT: Ensure you have executed 'docker login' in your shell beforehand.${NC}"
read -p "Are you logged into Docker Hub? (y/n): " loginConfirm
if [ "$loginConfirm" != "y" ] && [ "$loginConfirm" != "yes" ]; then
    echo -e "${RED}[*] Please execute 'docker login' first, then run this script.${NC}"
    exit 1
fi

# 3. Perform tagging and pushing
echo -e "\n${GREEN}[*] Tagging unified GPU/CPU image...${NC}"
docker tag gauravraval/slm-trainer:gpucpu "${dockerHubUser}/slm-trainer:gpucpu"

echo -e "${GREEN}[*] Pushing unified GPU/CPU image to Docker Hub...${NC}"
docker push "${dockerHubUser}/slm-trainer:gpucpu"

echo -e "\n${GREEN}[✓] Image successfully pushed to: https://hub.docker.com/r/${dockerHubUser}/slm-trainer${NC}"
echo -e "${CYAN}=======================================================================${NC}"
echo -e "${CYAN}🎉 DEPLOYMENT ASSISTANT COMPLETED!${NC}"
echo -e "${CYAN}=======================================================================${NC}"
