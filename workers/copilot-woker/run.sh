#!/bin/bash

set -euo pipefail

echo "Starting the worker script..."

echo "Preparing the environment..."
git config --global user.name "AI Bot"
git config --global user.email "ai-dev-bot@nxtgencollab.com"

: "${TASK_ID:?TASK_ID is required}"
: "${TASK_TITLE:?TASK_TITLE is required}"
: "${TASK_DESCRIPTION:?TASK_DESCRIPTION is required}"

cat > /opt/task.json <<EOF
{
  "id": "$TASK_ID",
  "title": "$TASK_TITLE",
  "description": "$TASK_DESCRIPTION"
}
EOF

echo "Task information populated dynamically."
echo "Task ID: $TASK_ID"
echo "Task Title: $TASK_TITLE"

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

echo "Cleaning generated development artifacts..."
rm -rf .venv
rm -rf __pycache__
rm -rf .pytest_cache
rm -rf .mypy_cache
rm -rf .ruff_cache

git status
git add .

if git diff --cached --quiet; then
    echo "No changes to commit."
else
    git commit -m "Task $TASK_ID implemented"
    git push origin feat/$TASK_ID
fi

echo "Step-4(End): Changes committed and pushed."
echo "Step-5(Start): Create a pull request..."
gh pr create --title "Feat: $TASK_ID - $TASK_TITLE" --body "This pull request implements task $TASK_ID: $TASK_DESCRIPTION" --head feat/$TASK_ID
echo "Step-5(End): Pull request created."

echo "Worker script completed successfully..."