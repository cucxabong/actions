# How to add/modify actions
## Update 'config.yml' to add new upstream repo or update new commit hash

The `config.yml` file contains the mapping of upstream actions repositories and their corresponding commit hashes that we track. To add a new repository or update an existing one:

1. Open `config.yml`
2. To add a new action:
   ```yaml
   upstreams:
    - repo: owner/repo
      commit: "abc123..."  # Specify the commit hash you want to track
   ```
3. To update an existing repository, simply update its commit hash value


## Running script to create new/update existing composite actions

The `update.py` script helps automate the process of creating and updating composite actions based on the configuration in `config.yml`.

```shell
# Make sure you're in the root folder
cd $(git rev-parse --show-toplevel)

# Install required dependencies
pip install requests pyyaml

# Run the update script
python update.py
```

The script will:
1. Read the configuration from `config.yml`
2. Fetch the specified repositories at their defined commit hashes
3. Create or update the composite actions by fetching remote 'action.yml' and update composite actions accordingly


## Create MR to update 'main' branch

After making your changes:

1. Create a new branch for your changes:
   ```shell
   git checkout -b update-actions
   ```

2. Commit your changes:
   ```shell
   git add .
   git commit -m "Update composite actions"
   ```

3. Push your changes and create a Merge Request (MR):
   ```shell
   git push -u origin update-actions
   ```

4. Go to your repository's web interface and create a new MR targeting the `main` branch

Note: Make sure to test your changes before submitting the MR.


# Using actions from this repo

Update your workflow by prefixing 3rd upstream with your `OWNER/REPO` and desired commit/branch. For example:
```shell
name: Your awesome workflow
on:
  pull_request:
jobs:
  preview:
    name: Your awesome workflow
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: 'stable'

      - run: go mod download
```

**TO**
```shell
name: Your awesome workflow
on:
  pull_request:
jobs:
  preview:
    name: Your awesome workflow
    runs-on: ubuntu-latest
    steps:
      - uses: cucxabong/actions/actions/checkout@main

      - uses: cucxabong/actions/actions/setup-go@2edd9b....
        with:
          go-version: 'stable'

      - run: go mod download
```

# Limitations

* Composite actions will not work with dynamic outputs. If [downstream workflows need outputs from actions that uses](https://github.com/orgs/community/discussions/10529) `core.setOutput` to set dynamic outputs based on runtime configuration and is not well defined in upstream actions's `action.yml`, please use upstream actions directly.
