# gen_semver
Bump semantic version based on GitLab merge request label.

This python script is meant to be run after a merge request in GitLab is completed.

Based on the label the merge request has recveied the script will bump the semantic version and create a new git tag. The script will also modify the version value in package.json
