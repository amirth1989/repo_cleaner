from github import Github
from datetime import datetime, timedelta
import os

# Constants
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Set your GitHub token as an environment variable
TIME_WINDOW_DAYS = 365  # Time window in days (1 year)
MASTER_REPO_LIST = "masterRepoList.txt"

# Initialize GitHub API
g = Github(GITHUB_TOKEN)

def get_repo_list():
    """Read the list of repositories from masterRepoList.txt."""
    try:
        with open(MASTER_REPO_LIST, "r") as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print(f"Error: {MASTER_REPO_LIST} not found.")
        return []

def get_stale_branches(repo, time_window):
    """Identify branches older than the specified time window."""
    stale_branches = []
    cutoff_date = datetime.utcnow() - timedelta(days=time_window)
    
    try:
        for branch in repo.get_branches():
            last_commit_date = branch.commit.commit.author.date
            if last_commit_date < cutoff_date:
                stale_branches.append(branch.name)
    except Exception as e:
        print(f"Error retrieving branches for {repo.full_name}: {e}")
    
    return stale_branches

def delete_branches(repo, branches_to_delete):
    """Delete selected branches."""
    for branch in branches_to_delete:
        try:
            ref = repo.get_git_ref(f"heads/{branch}")
            ref.delete()
            print(f"Deleted branch: {branch}")
        except Exception as e:
            print(f"Error deleting branch {branch} in {repo.full_name}: {e}")

def main():
    # Read repository list
    repo_urls = get_repo_list()
    deleted_branches_summary = {}

    if not repo_urls:
        print("No repositories found. Exiting.")
        return

    for repo_url in repo_urls:
        repo_name = "/".join(repo_url.split("/")[-2:])  # Extract owner/repo format
        
        try:
            repo = g.get_repo(repo_name)
        except Exception as e:
            print(f"Error accessing repository {repo_name}: {e}")
            continue

        # Get stale branches
        stale_branches = get_stale_branches(repo, TIME_WINDOW_DAYS)
        total_branches = sum(1 for _ in repo.get_branches())

        print(f"\nRepository: {repo_name}")
        print(f"Total branches: {total_branches}")
        print(f"Stale branches: {len(stale_branches)}")

        if stale_branches:
            print("Stale branches:")
            for i, branch in enumerate(stale_branches, 1):
                print(f"{i}. {branch}")

            # Get user input for deletion
            while True:
                user_input = input("Enter branch numbers to delete (comma-separated, 'all' to delete all, 'none' to skip): ").strip().lower()
                if user_input == "all":
                    branches_to_delete = stale_branches
                    break
                elif user_input == "none":
                    branches_to_delete = []
                    break
                else:
                    try:
                        selected_indices = [int(i) - 1 for i in user_input.split(",")]
                        if all(0 <= i < len(stale_branches) for i in selected_indices):
                            branches_to_delete = [stale_branches[i] for i in selected_indices]
                            break
                        else:
                            print("Invalid selection. Please enter valid branch numbers.")
                    except ValueError:
                        print("Invalid input. Please enter numbers separated by commas.")

            # Delete branches
            if branches_to_delete:
                delete_branches(repo, branches_to_delete)
                deleted_branches_summary[repo_name] = branches_to_delete

    # Generate executive summary
    if deleted_branches_summary:
        print("\nExecutive Summary:")
        for repo, branches in deleted_branches_summary.items():
            print(f"Repository: {repo}")
            print(f"Deleted branches: {', '.join(branches)}")
            if len(branches) == total_branches:
                print("Recommendation: Consider deleting the repository as all branches were stale.")

if _name_ == "_main_":
    main()
