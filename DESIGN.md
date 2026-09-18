Task: Add a footer to all the webpages

docker-container:
# checkout the source code
    - checkout source code (git clone <repository_url>)
# run the copilot command to perform the task
    - copilot -p "task: Add a footer to all the webpages"
# publish the changes
    - git status
    - git add .
    - git commit -m "Add footer to all the webpages"
    - git push -u origin feat/task-<id>
# create a pull request
    - gh pr create --title "Add footer to all the webpages" --body "This PR adds a footer to all the webpages." --base main --head feat/task-<id>