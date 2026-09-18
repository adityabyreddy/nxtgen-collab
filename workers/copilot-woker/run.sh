#!/bin/bash

set -euo pipefail

echo "Starting the worker script..."

echo "Preparing the environment..."
git config --global user.name "AI Bot"
git config --global user.email "ai-dev-bot@nxtgencollab.com"

TASK_ID=$(jq -r '.id' /opt/task.json)
TASK_TITLE=$(jq -r '.title' /opt/task.json)
TASK_DESCRIPTION=$(jq -r '.description' /opt/task.json)

echo "Step-1(Start): Cloning the repository..."
gh repo clone adityabyreddy/goal-manager $PROJECT_WORKDIR

# TODO: Construct the URL dynamically based on the given project
git remote set-url origin https://x-access-token:$GH_TOKEN@github.com/adityabyreddy/goal-manager.git

git branch feat/$TASK_ID
git checkout feat/$TASK_ID
git status
echo "Step-1(End): Repository cloned."

echo "Step-2(Start): Reading the task from task.json..."
TASK=$(cat /opt/task.json)
echo "Step-2(End): Task read as '$TASK'."

echo "Step-3(Start): Executing the task..."
copilot -p "$(cat /opt/task.json)" --allow-all
echo "Step-3(End): Task executed."

echo "Step-4(Start): Committing and pushing changes..."
git status
git add .
git commit -m "Task $TASK_ID implemented"
git push origin feat/$TASK_ID
echo "Step-4(End): Changes committed and pushed."

echo "Step-5(Start): Create a pull request..."
gh pr create --title "Feat: $TASK_ID - $TASK_TITLE" --body "This pull request implements task $TASK_ID: $TASK_DESCRIPTION" --head feat/$TASK_ID
echo "Step-5(End): Pull request created."

echo "Worker script completed successfully..."