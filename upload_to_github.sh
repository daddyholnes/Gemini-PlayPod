#!/bin/bash

# Create a temporary directory for the clean repository
mkdir -p clean-repo-temp
tar -xzf clean-repo.tar.gz -C clean-repo-temp
cd clean-repo-temp

# Initialize a new Git repository
git init
git config --local user.email "your-email@example.com"
git config --local user.name "Your Name"

# Copy .gitignore and add files to Git
cp ../.gitignore .
git add .
git commit -m "Initial commit with clean repository"

# Add the GitHub repository as a remote
echo "Please enter your GitHub Personal Access Token:"
read -s GITHUB_TOKEN
git remote add origin https://$GITHUB_TOKEN@github.com/daddyholnes/Gemini-PlayPod.git

# Push to GitHub with force (be careful with this!)
git push -f origin main

echo "Done! Your code has been pushed to GitHub."