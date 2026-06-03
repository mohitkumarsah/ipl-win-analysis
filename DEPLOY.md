Deployment instructions

This file explains how to push the project to your GitHub repo and deploy it.

1) Connect local repo to your GitHub repository

# Using HTTPS (recommended with GitHub CLI or personal access token)
```bash
# initialize git if not already done
git init
git add .
git commit -m "Initial commit: add IPL dashboard"

# add your GitHub repo as origin (replace with your repo)
git remote add origin https://github.com/mohitkumarsah/ipl-win-analysis.git

# create main branch and push
git branch -M main
git push -u origin main
```

If you get authentication errors, use `gh` to login first:
```bash
gh auth login
```

# Using SSH (if your SSH key is configured)
```bash
git remote add origin git@github.com:mohitkumarsah/ipl-win-analysis.git
git branch -M main
git push -u origin main
```

2) Deploy options

- Streamlit Community Cloud (fastest):
  - Push repo to GitHub, then go to https://share.streamlit.io and create a new app. Select your repo, branch `main`, and set `Main file` to `app.py`.

- Render (easy web service):
  - Create an account, New -> Web Service -> connect GitHub -> select repo.
  - Build command: `pip install -r requirements.txt`
  - Start command: `streamlit run app.py --server.port $PORT`
  - Use the `Procfile` included in this repo if you prefer.

- Docker (portable):
  - Build image locally:
    ```bash
    docker build -t ipl-dashboard .
    docker run -p 8501:8501 ipl-dashboard
    ```
  - To deploy to cloud, push the image to Docker Hub or your cloud registry and run using your provider.

- Other clouds (AWS/GCP/Azure):
  - Use the provided `Dockerfile` for container-based deployments (Cloud Run, ECS, Azure Web App for Containers).

3) Notes & troubleshooting
- Ensure `requirements.txt` lists all dependencies (update if you add packages).
- If you want scikit-learn used on the server, ensure `scikit-learn` is in `requirements.txt` (it already is).
- If large CSVs cause slow startup, consider using a remote data store or preprocessed smaller CSV for deploy.

