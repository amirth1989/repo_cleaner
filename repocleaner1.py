from github import Github
from datetime import datetime, timedelta
import os

# Constants
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Retrieve token from environment variable
TW = 30  # Time window (days) for stale branches
MASTER_REPO_LIST = "masterRepoList.txt"

# Initialize GitHub API
if not GITHUB_TOKEN:
    raise ValueError("GitHub token not found. Set it as an environment variable.")
g = Github(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git)


def get_repo_list():
    """Read the list of repositories from masterRepoList.txt."""
    with open(MASTER_REPO_LIST, "r") as file:
        return [line.strip() for line in file.readlines()]

def get_stale_branches(repo, time_window):
    """Identify branches older than the time window."""
    stale_branches = []
    now = datetime.utcnow()  # Ensure we use UTC to match GitHub's timestamp

    for branch in repo.get_branches():
        try:
            last_commit_date = branch.commit.commit.author.date.replace(tzinfo=None)  # Convert to naive datetime
            if (now - last_commit_date).days > time_window:
                stale_branches.append(branch.name)
        except Exception as e:
            print(f"Error retrieving commit date for branch {branch.name}: {e}")
    
    return stale_branches

def delete_branches(repo, branches_to_delete):
    """Delete selected branches."""
    for branch in branches_to_delete:
        try:
            ref = repo.get_git_ref(f"heads/{branch}")
            ref.delete()
            print(f"Deleted branch: {branch}")
        except Exception as e:
            print(f"Failed to delete branch {branch}: {e}")

def main():
    repo_urls = get_repo_list()
    deleted_branches_summary = {}

    for repo_url in repo_urls:
        try:
            repo_name = repo_url.split("/")[-1]
            owner_name = repo_url.split("/")[-2]  # Extract owner from URL
            repo = g.get_repo(f"{owner_name}/{repo_name}")

            # Get stale branches
            stale_branches = get_stale_branches(repo, TW)
            print(f"\nRepository: {repo_name}")
            print(f"Total branches: {len(list(repo.get_branches()))}")  # Convert to list to get count
            print(f"Stale branches: {len(stale_branches)}")

            if stale_branches:
                print("Stale branches:")
                for i, branch in enumerate(stale_branches, 1):
                    print(f"{i}. {branch}")

                # Get user consent for deletion
                user_input = input("Enter branch numbers to delete (comma-separated, 'all' to delete all, 'none' to skip): ")
                if user_input.lower() == "all":
                    branches_to_delete = stale_branches
                elif user_input.lower() == "none":
                    branches_to_delete = []
                else:
                    try:
                        selected_indices = [int(i) - 1 for i in user_input.split(",") if i.strip().isdigit()]
                        branches_to_delete = [stale_branches[i] for i in selected_indices if 0 <= i < len(stale_branches)]
                    except ValueError:
                        print("Invalid input. No branches deleted.")
                        branches_to_delete = []

                # Delete branches
                if branches_to_delete:
                    delete_branches(repo, branches_to_delete)
                    deleted_branches_summary[repo_name] = branches_to_delete

        except Exception as e:
            print(f"Error processing repository {repo_url}: {e}")

    # Generate executive summary
    print("\nExecutive Summary:")
    for repo, branches in deleted_branches_summary.items():
        print(f"Repository: {repo}")
        print(f"Deleted branches: {', '.join(branches)}")
        if len(branches) == len(list(repo.get_branches())):
            print("Recommendation: Consider deleting the repository as all branches were stale.")

if __name__ == "__main__":
    main()
