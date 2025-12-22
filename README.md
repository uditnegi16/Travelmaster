Python version=3.12

Package manager - Uv

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