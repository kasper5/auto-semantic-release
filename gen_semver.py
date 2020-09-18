#!/usr/bin/env python3
import os
import re
import sys
import json
import subprocess
import semver
import gitlab


def git(*args):
    return subprocess.check_output(["git"] + list(args))


def extract_merge_request_id_from_commit():
    message = git("log", "-1", "--pretty=%B")
    matches = re.search(r'(\S*\/\S*!)(\d+)', message.decode("utf-8"), re.M | re.I)

    if matches is None:
        raise Exception(f"Unable to extract merge request id from commit message: {message}")

    return matches.group(2)


def retrieve_labels_from_merge_request(merge_request_id):
    project_id = os.environ['CI_PROJECT_ID']
    gitlab_private_token = os.environ['PRIVATE_TOKEN']

    gl = gitlab.Gitlab(os.environ['CI_SERVER_URL'], private_token=gitlab_private_token)
    gl.auth()

    project = gl.projects.get(project_id)
    merge_request = project.mergerequests.get(merge_request_id)

    return merge_request.labels


def update_package_json(version):
    with open('package.json', 'r') as file:
        json_data = json.load(file)
        json_data['version'] = version

    with open('package.json', 'w') as file:
        json.dump(json_data, file, indent=2)


def push_repo(version):
    push_dst = "HEAD" + ":" + os.environ['CI_COMMIT_REF_NAME']
    cmt_msg = "release " + version + " [ci skip]"

    git("add", "-f", "package.json")
    git("commit", "-m", cmt_msg)
    git("push", "origin", push_dst)


def tag_repo(tag):
    url = os.environ["CI_REPOSITORY_URL"]
    push_url = re.sub(r'.+@([^/]+)/', r'git@\1:', url)

    git("remote", "set-url", "--push", "origin", push_url)
    git("tag", tag)
    git("push", "origin", tag)


def bump_version(latest):
    merge_request_id = extract_merge_request_id_from_commit()
    labels = retrieve_labels_from_merge_request(merge_request_id)

    if "bump::major" in str(labels):
        bump = semver.bump_major(latest)
    elif "bump::minor" in str(labels):
        bump = semver.bump_minor(latest)
    else:
        bump = semver.bump_patch(latest)

    return bump


def main():
    try:
        latest = git("describe", "--tags").decode().strip()
    except subprocess.CalledProcessError:
        # No tags in the repository
        version = "1.0.0"
    else:
        # Skip already tagged commits
        if '-' not in latest:
            print(latest)
            return 0

        version = bump_version(latest)

    update_package_json(version)
    push_repo(version)
    tag_repo(version)
    print(version)

    return 0


if __name__ == "__main__":
    sys.exit(main())
