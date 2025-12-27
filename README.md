# 🚀 Setup the Project

1. Clone the repo (if not already done)

   ```bash
   git clone https://git.indexnine.com/idx9-internal/seeds/Python/python-fast-api-seed.git
   cd python-fast-api-seed
   ```

2. Create a .env file in the root directory (copy from .env.example):

   ```bash
   cp .env.example .env
   ```

3. Setup pre-commit hook for formatting and linting.

   ```
   chmod +x ./scripts/setup-hooks.sh

   ./scripts/setup-hooks.sh
   ```

4. Activate the environment

   ```bash
   # On macOS/Linux
   source .venv/bin/activate

   # On Windows
   .venv\Scripts\activate

   ```

5. Install dependencies using uv

   ```bash
   # Install curl (needed for uv install script)
   RUN apt-get update && apt-get install -y curl

   # Install uv
   RUN curl -Ls https://astral.sh/uv/install.sh | sh

   uv add -r requirements.txt
   uv add -r requirements-dev.txt

   # To lock the dependencies
   uv lock

   # To fix lint, imports and auto fix etc.
   ruff check . --fix
   ```

6. Run the application (example)

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

# python-fast-api-seed service

**Edit a file, create a new file, and clone from Bitbucket in under 2 minutes**

When you're done, you can delete the content in this README and update the file with details for others getting started with your repository.

_We recommend that you open this README in another tab as you perform the tasks below. You can [watch our video](https://youtu.be/0ocf7u76WSo) for a full demo of all the steps in this tutorial. Open the video in a new tab to avoid leaving Bitbucket._

---

## Edit a file

You’ll start by editing this README file to learn how to edit a file in Bitbucket.

1. Click **Source** on the left side.
2. Click the README.md link from the list of files.
3. Click the **Edit** button.
4. Delete the following text: _Delete this line to make a change to the README from Bitbucket._
5. After making your change, click **Commit** and then **Commit** again in the dialog. The commit page will open and you’ll see the change you just made.
6. Go back to the **Source** page.

---

## Create a file

Next, you’ll add a new file to this repository.

1. Click the **New file** button at the top of the **Source** page.
2. Give the file a filename of **contributors.txt**.
3. Enter your name in the empty file space.
4. Click **Commit** and then **Commit** again in the dialog.
5. Go back to the **Source** page.

Before you move on, go ahead and explore the repository. You've already seen the **Source** page, but check out the **Commits**, **Branches**, and **Settings** pages.

---

## Clone a repository

Use these steps to clone from SourceTree, our client for using the repository command-line free. Cloning allows you to work on your files locally. If you don't yet have SourceTree, [download and install first](https://www.sourcetreeapp.com/). If you prefer to clone from the command line, see [Clone a repository](https://confluence.atlassian.com/x/4whODQ).

1. You’ll see the clone button under the **Source** heading. Click that button.
2. Now click **Check out in SourceTree**. You may need to create a SourceTree account or log in.
3. When you see the **Clone New** dialog in SourceTree, update the destination path and name if you’d like to and then click **Clone**.
4. Open the directory you just created to see your repository’s files.

Now that you're more familiar with your Bitbucket repository, go ahead and add a new file locally. You can [push your change back to Bitbucket with SourceTree](https://confluence.atlassian.com/x/iqyBMg), or you can [add, commit,](https://confluence.atlassian.com/x/8QhODQ) and [push from the command line](https://confluence.atlassian.com/x/NQ0zDQ).

## Sonarqube execution steps

```
pysonar --sonar-host-url=<sonarqube_host_value> --token=<token_value>
```

## Features

- [x] API Documentation (Built in Swagger UI)
- [x] Cursor Rules (Basic Rules)
- [x] Database ORM & Migrations (PostgreSQL + SQLAlchemy)
- [x] Logger
- [x] SonarQube
- [x] Pre Commit hooks
- [x] Docker Compose (to generate dynamic environments dev,prod,staging based on .env file)
- [x] Request Context
- [x] Middleware
- [x] Rate Limiting (Limiter)
- [x] JWKS (JSON Web Key Set)
- [x] Authentication (JWKS)
- [x] Request Validation (Pydantic Schema)
- [x] Caching (in-memory OR Redis based on env config)
- [ ] Unit Testing
- [ ] CI/CD (GitHub Actions)
- [ ] Multi Media Management
- [ ] Secret Management
- [ ] Multi Tenancy
- [ ] Cloud Storage (S3, etc.)
- [ ] SSO (Single Sign On)
- [ ] Observability
- [ ] Encryption & Decryption
- [ ] Notification Service
- [ ] Authorization (RBAC, PBAC, PABAC)
