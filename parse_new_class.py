"""This script parses a pull request for new class definitions
and generates a report of the new classes found."""

import os
import subprocess

import coverage

# base_commit = "3f3e58e6212c3463c38ca6b1d78d15cd3d78f39e"
# head_commit = "e053f9d9402079fb62ea40aca8f7c268b9f71294"
base_commit = os.environ.get("BASE_COMMIT", None)
head_commit = os.environ.get("HEAD_COMMIT", None)
if not base_commit or not head_commit:
    raise ValueError("BASE_COMMIT and HEAD_COMMIT environment variables must be set.")


def get_pr_commits(base_sha, head_sha):
    """Get list of commit SHAs between base and head"""
    try:
        result = subprocess.run(
            ["git", "rev-list", f"{base_sha}..{head_sha}"],
            capture_output=True,
            text=True,
            check=True,
        )
        commits = result.stdout.strip().split("\n")
        return [commit for commit in commits if commit]  # Filter empty strings
    except subprocess.CalledProcessError as e:
        print(f"Error getting commits: {e}")
        return []


def parse_new_classes(commit_sha):
    """Parse a commit for new class definitions"""
    try:
        result = subprocess.run(
            ["git", "show", commit_sha], capture_output=True, text=True, check=True
        )
        changes = result.stdout
        file_data = changes.split("diff --git")

        new_classes_in_files = {}
        for file_data in file_data:
            if "class " in file_data:
                class_name = None
                file_name = None
                for line in file_data.splitlines():
                    if "class " in line:
                        # Extract class name
                        class_name = line.split("class ")[1].split("(")[0].strip()
                    if line.startswith("+++ b/"):
                        file_name = line[6:].strip()
                        if "adi/" not in file_name:  # Only take part classes
                            file_name = None
                if class_name and file_name:
                    if file_name not in new_classes_in_files:
                        new_classes_in_files[file_name] = []
                    new_classes_in_files[file_name].append(class_name)

        return new_classes_in_files

    except subprocess.CalledProcessError as e:
        print(f"Error parsing commit {commit_sha}: {e}")
        return []


# Usage
base = base_commit
head = head_commit
commits = get_pr_commits(base, head)
print(f"Found {len(commits)} commits:")
all_new_classes = {}
for commit in commits:
    print(commit)
    new_classes = parse_new_classes(commit)
    if new_classes:
        for file, classes in new_classes.items():
            if file not in all_new_classes:
                all_new_classes[file] = []
            for class_name in classes:
                if class_name not in all_new_classes[file]:
                    all_new_classes[file].append(class_name)

print("\nSummary of new classes found:")
for file, classes in all_new_classes.items():
    if classes:
        print(f"{file}: {', '.join(classes)}")


converage_file = ".coverage"

cov = coverage.Coverage(data_file=converage_file)
cov.load()
cov.report(show_missing=True, ignore_errors=True)
# cov.html_report(directory="htmlcov", ignore_errors=True)
# cov.xml_report(outfile="coverage.xml", ignore_errors=True)

# Parse the coverage data for new classes
new_classes_coverage = {}
for file, classes in all_new_classes.items():
    if classes:
        for class_name in classes:
            if class_name not in new_classes_coverage:
                analysis = cov.analysis2(file)

                filename, executed, excluded, notrun, missing = analysis

                print(f"File: {filename}")
                print(f"Executed lines: {executed}")
                print(f"Missing lines: {missing}")
                print(f"Not run lines: {notrun}")
                total_lines = len(executed) + len(missing) + len(notrun)
                coverage_percentage = (
                    len(executed) / total_lines * 100 if total_lines > 0 else 0
                )
                print(f"Coverage percentage: {coverage_percentage:.2f}%")
                new_classes_coverage[class_name] = {
                    "file": file,
                    "coverage_percentage": coverage_percentage,
                }


def comment_pr(class_coverage_summary):
    """Add comment to github PR with class coverage summary"""
    message = "### New Classes Coverage Summary\n\n"
    message += "| Class Name | File | Coverage Percentage |\n"
    message += "|------------|------|---------------------|\n"
    for class_name, data in class_coverage_summary.items():
        message += (
            f"| {class_name} | {data['file']} | {data['coverage_percentage']:.2f}% |\n"
        )

    print("Adding comment to PR with coverage summary...")
    print(message)
    pr_number = os.environ.get("PR_NUMBER")
    if pr_number:
        subprocess.run(
            ["gh", "pr", "comment", pr_number, "--body", message], check=True
        )


comment_pr(new_classes_coverage)


def fail_pr(class_coverage_summary, threshold=70):
    """Fail the PR if coverage is below threshold"""
    for class_name, data in class_coverage_summary.items():
        if data["coverage_percentage"] < threshold:
            print(
                f"Class {class_name} in file {data['file']} has coverage {data['coverage_percentage']:.2f}% which is below the threshold of {threshold}%"
            )
            raise ValueError(
                f"Class {class_name} in file {data['file']} has coverage {data['coverage_percentage']:.2f}% which is below the threshold of {threshold}%"
            )


fail_pr(new_classes_coverage, threshold=70)
