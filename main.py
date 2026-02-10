import os
import sys
from github import Github
from dotenv import load_dotenv
from colorama import Fore, Style, init
from ai_engine import analyze_code

# Initialize colors for terminal output
init(autoreset=True)
load_dotenv()

# Get GitHub Token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print(f"{Fore.RED}Error: GITHUB_TOKEN is missing in .env{Style.RESET_ALL}")
    sys.exit(1)

def post_comment(pr, filename, commit, line, message):
    """
    Posts a comment on a specific line of the PR.
    """
    try:
        # We use create_review_comment to post ON the code line
        pr.create_review_comment(
            body=message,
            commit_id=commit,
            path=filename,
            line=int(line), # Ensure line is an integer
            side="RIGHT"    # Comment on the 'new' version of the code
        )
        print(f"{Fore.GREEN}✔ Posted comment on {filename} line {line}{Style.RESET_ALL}")
    except Exception as e:
        # Common Error: You can't comment on lines that weren't changed in the PR!
        print(f"{Fore.RED}✘ Failed to post on {filename}:{line}. (GitHub only allows comments on changed lines){Style.RESET_ALL}")
        # Optional: specific error printing for debugging
        # print(e)

def get_pr_details(repo_name, pr_number):
    """
    Fetches the PR and the specific Commit ID needed for commenting.
    """
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    print(f"{Fore.CYAN}Fetching PR #{pr_number} from {repo_name}...{Style.RESET_ALL}")
    
    # CRITICAL: We need the specific commit ID to attach comments to
    commits = list(pr.get_commits())
    latest_commit = commits[-1] # Get the very last commit

    files_data = []
    
    for file in pr.get_files():
        # Skip deleted files or non-code files
        if file.status == "removed" or not file.filename.endswith(('.py', '.js', '.ts', '.tsx')):
            continue

        try:
            # Get full content to give the AI context
            content_file = repo.get_contents(file.filename, ref=latest_commit.sha)
            full_content = content_file.decoded_content.decode("utf-8")
            
            files_data.append({
                "filename": file.filename,
                "diff": file.patch,
                "full_content": full_content,
                "commit": latest_commit, # Pass the commit object for commenting later
                "pr_object": pr
            })
        except Exception as e:
            print(f"{Fore.YELLOW}Skipping {file.filename}: {e}{Style.RESET_ALL}")

    return files_data

def main():
    # USAGE: python main.py owner/repo 1
    if len(sys.argv) < 3:
        print("Usage: python main.py <owner/repo> <pr_number>")
        sys.exit(1)

    repo_name = sys.argv[1]
    pr_number = int(sys.argv[2])

    files = get_pr_details(repo_name, pr_number)
    
    if not files:
        print(f"{Fore.YELLOW}No supported code files found to review.{Style.RESET_ALL}")
        return

    for file in files:
        print(f"\nAnalyzing: {Fore.YELLOW}{file['filename']}{Style.RESET_ALL}...")
        
        # 1. Ask the AI
        result = analyze_code(file['filename'], file['diff'], file['full_content'])
        reviews = result.get("reviews", [])
        
        if not reviews:
            print(f"{Fore.GREEN}No issues found.{Style.RESET_ALL}")
        
        # 2. Post Comments
        for review in reviews:
            line_num = review['line']
            issue_desc = review['issue']
            fix_code = review['fix']
            severity = review.get('severity', 'medium')

            # Print to terminal
            print(f"{Fore.MAGENTA}Found issue on line {line_num}: {issue_desc}{Style.RESET_ALL}")
            
            # Format the comment elegantly for GitHub
            comment_body = (
                f"### 🤖 AI Code Reviewer\n"
                f"**Severity:** {severity.upper()}\n\n"
                f"**Issue:** {issue_desc}\n\n"
                f"**Suggested Fix:**\n"
                f"```python\n{fix_code}\n```"
            )
            
            # Send to GitHub
            post_comment(
                file['pr_object'], 
                file['filename'], 
                file['commit'], 
                line_num, 
                comment_body
            )

if __name__ == "__main__":
    main()