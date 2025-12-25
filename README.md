# Python version=3.12

# Package manager - Uv
    Commands: 
    uv init
    uv help
    uv venv --python 3.12
    uv add [library]
    uv pip install -r requirements.txt
    uv sync

---

# 📦 UV Package Manager – Detailed Guide

`uv` is a **modern, ultra-fast Python package manager** that replaces or complements:

* `pip`
* `pip-tools`
* `virtualenv`
* parts of `poetry`

It is written in **Rust**, making it **much faster and more reliable** than traditional tools.

---

## 🧠 Key Concepts (Before the Table)

| Concept                    | Meaning                                      |
| -------------------------- | -------------------------------------------- |
| **Project Initialization** | Sets up Python project metadata              |
| **Virtual Environment**    | Isolated Python environment for dependencies |
| **Dependency Management**  | Adding, syncing, and locking libraries       |
| **Reproducibility**        | Ensures same dependencies across machines    |

---

## 📋 UV Commands – Expanded Explanation Table

| Step  | Command                              | Purpose                        | What It Does Internally                                 | When to Use                     |
| ----- | ------------------------------------ | ------------------------------ | ------------------------------------------------------- | ------------------------------- |
| **1** | `uv init`                            | Initialize a Python project    | Creates project metadata like `pyproject.toml`          | First time setting up a project |
| **2** | `uv help`                            | Get help & command list        | Displays all available `uv` commands and options        | When learning or stuck          |
| **3** | `uv venv --python 3.12`              | Create virtual environment     | Creates a `.venv/` using Python 3.12                    | Before installing dependencies  |
| **4** | `uv add [library]`                   | Add a dependency               | Installs package + updates `pyproject.toml` & lock file | When adding new libraries       |
| **5** | `uv pip install -r requirements.txt` | Install from requirements file | Uses `uv`'s fast resolver instead of pip                | Migrating old projects          |
| **6** | `uv sync`                            | Sync environment               | Installs exact versions from lock file                  | Team collaboration / CI         |

---

## 🔍 Deep Explanation (Command by Command)

---

### 🔹 `uv init`

```bash
uv init
```

**What it does:**

* Initializes a Python project
* Creates:

  * `pyproject.toml`
  * Project metadata (name, version, dependencies)

**Why it matters:**

* This is the **foundation** for dependency management
* Similar to `poetry init`

---

### 🔹 `uv help`

```bash
uv help
```

**What it does:**

* Lists all `uv` commands
* Shows subcommands and options

**Best use case:**

* Learning `uv`
* Debugging command syntax

---

### 🔹 `uv venv --python 3.12`

```bash
uv venv --python 3.12
```

**What it does:**

* Creates a virtual environment using Python 3.12
* Stores it in `.venv/`

**Why this is powerful:**

* Ensures **consistent Python version**
* No need for `virtualenv` or `conda`

✅ Recommended for production projects

---

### 🔹 `uv add [library]`

```bash
uv add numpy
```

**What it does:**

* Installs the library
* Updates:

  * `pyproject.toml`
  * `uv.lock` (dependency lock file)

**Why this is better than `pip install`:**

* Dependency versions are **locked**
* Prevents “works on my machine” issues

---

### 🔹 `uv pip install -r requirements.txt`

```bash
uv pip install -r requirements.txt
```

**What it does:**

* Installs dependencies from `requirements.txt`
* Uses `uv`'s **fast resolver**

**Best for:**

* Migrating existing `pip` projects
* Legacy projects

---

### 🔹 `uv sync`

```bash
uv sync
```

**What it does:**

* Reads the lock file
* Installs **exact versions** of all dependencies

**Why this is critical for teams:**

* Every developer gets **identical environments**
* Essential for:

  * CI/CD
  * Production
  * Team collaboration

---

## 🧪 Recommended Workflow (Best Practice)

```bash
uv init
uv venv --python 3.12
source .venv/bin/activate   # (Linux/Mac)
.venv\Scripts\activate      # (Windows)

uv add django
uv add pandas
uv sync
```

---

## 🆚 UV vs Traditional Tools (Quick Comparison)

| Feature             | pip    | poetry    | uv            |
| ------------------- | ------ | --------- | ------------- |
| Speed               | ❌ Slow | ⚠️ Medium | ✅ Very Fast   |
| Lock file           | ❌ No   | ✅ Yes     | ✅ Yes         |
| Virtual env         | ❌ No   | ✅ Yes     | ✅ Yes         |
| Dependency resolver | ❌ Weak | ✅ Strong  | ✅ Very Strong |
| CI-friendly         | ⚠️     | ✅         | ✅✅            |

---

## 📌 One-Line Summary
> **UV is a high-performance Python package manager that combines dependency resolution, virtual environments, and reproducibility into a single fast tool.**

---


----------------------
Agile Framework- Jira

- Include keys in your commit messages to link them to your Jira work items. 
- git commit -m "DEV-8 Status 1: Project Phase Finalization"

## 🧑‍💻 GitHub Workflow and Commands


| Step | Who | Action/Purpose | GitHub Command/Action |
| :--- | :--- | :--- | :--- |
| **1. Set up** | Team Member | **Clone the repository** to their local machine. | `git clone [repo_url]` |
| **2. Update** | Team Member | **Create a new branch** for their feature/work. | `git checkout -b feature/my-new-agent` |
| **3. Develop** | Team Member | **Make code changes** and stage them. | `git add .` |
| **4. Commit** | Team Member | **Save changes** locally to their branch history. | `git commit -m "Implemented core agent logic"` |
| **5. Push** | Team Member | **Upload the new branch** to GitHub. | `git push origin feature/my-new-agent` |
| **6. Request Review** | Team Member | **Open a Pull Request (PR)** on GitHub, targeting `main`. | **GitHub UI Action:** Click the "Compare & pull request" button. |
| **7. Review** | **You (Reviewer)** | **Check the code** in the PR for errors, style, and logic. | **GitHub UI Action:** Go to the PR, review "Files changed," and add comments. |
| **8. Approve/Request Changes** | **You (Reviewer)** | **Submit your formal review** (approval is required for merge). | **GitHub UI Action:** Click "Review changes" $\rightarrow$ select **"Approve"** or **"Request changes."** |
| **9. Merge** | **You (or Approved User)** | **Integrate the changes** into the protected `main` branch. | **GitHub UI Action:** Click the green **"Merge pull request"** button on the PR page (only active after approval). |
| **10. Cleanup** | Team Member | **Sync their local `main` branch** with the new changes. | `git checkout main` $\rightarrow$ `git pull origin main` |

---------------------------------------------------------------------

uttam's readme test



