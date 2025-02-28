from github import Github
from datetime import datetime, timedelta
import os
import subprocess
from collections import defaultdict

def read_repo_list(filename):
    with open(filename, "r") as file:
        return [line.strip() for line in file.readlines() if line.strip()]

def get_stale_branches(repo, time_window):
    stale_branches = []
    current_time = int(time.time())
    result = subprocess.run(["git", "ls-remote", "--heads", repo], capture_output=True, text=True)
    branches = [line.split()[-1].replace("refs/heads/", "") for line in result.stdout.strip().split("\n") if line]
    total_branches = len(branches)
    stale_count = 0
    
    for branch in branches:
        log_cmd = ["git", "log", "-1", "--format=%ct", f"origin/{branch}"]
        log_result = subprocess.run(log_cmd, capture_output=True, text=True)
        
        if log_result.stdout.strip():
            last_commit_time = int(log_result.stdout.strip())
            if (current_time - last_commit_time) > time_window:
                stale_days = (current_time - last_commit_time) // (24 * 60 * 60)
                stale_years = round(stale_days / 365, 2)
                stale_branches.append(f"{branch} ({stale_days} days, {stale_years} years)")
                stale_count += 1
    
    return stale_branches, total_branches, stale_count

def delete_branches(repo, branches):
    for branch in branches:
        branch_name = branch.split()[0]
        subprocess.run(["git", "push", repo, "--delete", branch_name])

def process_repositories(repo_list_file):
    time_window = 365 * 24 * 60 * 60  # 1 year in seconds
    repo_data = defaultdict(dict)
    
    repos = read_repo_list(repo_list_file)
    
    for repo in repos:
        print(f"Processing repository: {repo}")
        repo_name = os.path.basename(repo).replace(".git", "")
        
        if os.path.isdir(repo_name):
            print("Repository already cloned. Updating...")
            os.chdir(repo_name)
            subprocess.run(["git", "fetch", "--all"])
        else:
            subprocess.run(["git", "clone", repo])
            os.chdir(repo_name)
        
        stale_branches, total_branches, stale_count = get_stale_branches(repo, time_window)
        repo_data[repo]["total_branches"] = total_branches
        repo_data[repo]["stale_branches"] = stale_branches
        repo_data[repo]["stale_count"] = stale_count
        
        os.chdir("..")
    
    return repo_data

def display_summary(repo_data):
    print("Summary of repositories:")
    for repo, data in repo_data.items():
        print(f"Repository: {repo}")
        print(f"Total branches: {data['total_branches']}")
        print(f"Total stale branches: {data['stale_count']}")
        if data["stale_branches"]:
            print("Stale branches:")
            for branch in data["stale_branches"]:
                print(f"  - {branch}")
        else:
            print("No stale branches found.")
        print()

def prompt_for_deletion(repo_data):
    deleted_branches = defaultdict(list)
    
    for repo, data in repo_data.items():
        if not data["stale_branches"]:
            continue
        
        print(f"Stale branches found in repository: {repo}")
        for branch in data["stale_branches"]:
            print(f"  - {branch}")
        
        consent = input("Do you want to delete all, some, or none of the stale branches from this repo? (all/some/none): ").strip().lower()
        
        if consent == "all":
            delete_branches(repo, data["stale_branches"])
            deleted_branches[repo] = data["stale_branches"]
            print(f"Deleted all stale branches from {repo}.")
        elif consent == "some":
            selected_branches = input("Enter the branches you want to delete, separated by spaces: ").split()
            valid_branches = [b for b in data["stale_branches"] if b.split()[0] in selected_branches]
            if valid_branches:
                delete_branches(repo, valid_branches)
                deleted_branches[repo] = valid_branches
                print(f"Deleted selected stale branches from {repo}.")
            else:
                print("No valid stale branches selected for deletion.")
    
    return deleted_branches

def display_executive_summary(repo_data, deleted_branches):
    print("Executive Summary:")
    for repo, branches in deleted_branches.items():
        print(f"Repository: {repo}")
        print(f"Deleted branches: {', '.join(branches)}")
        if repo_data[repo]["total_branches"] == repo_data[repo]["stale_count"]:
            print("Recommendation: All branches in this repository are stale. Consider deleting the repository.")
        print()

def main():
    repo_list_file = "masterrepolist.txt"
    repo_data = process_repositories(repo_list_file)
    display_summary(repo_data)
    deleted_branches = prompt_for_deletion(repo_data)
    display_executive_summary(repo_data, deleted_branches)
    print("RepoCleaner run completed.")

if __name__ == "__main__":
    main()
