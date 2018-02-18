# pymgit

Clone a bunch of Git repositories to your machine to specified directories and
checkout a specific version (branch/tag).  When working with a lot of Git repos
and periodically moving to different machines, it is tedious to manually clone
all of the repositories you want.  It would be easier to have a text file list
the repositories and have a tool clone and checkout the repos in one fell
swoop.

**Note:** This program expects a modified form of an Ansible Galaxy style
requirements file (as this is the inspiration of this program) to contain the
list of repositories to clone, the version to checkout, and the destination
path to clone the repository.  See in examples below.

## Requirements

`python` and `git` installed on the machine that will run `pymgit`

## Assumptions

You have already handled the storage of your repository credentials in some
Git-way (e.g. SSH key, git credential helper, etc.) on the machine that will
run this program.  That is, this program won't be asking you for the location
of your keys (assume default/normal location) nor will it explicitly prompt
you for a password.  If you're checking out via https, the underlying `git`
program will likely prompt you for your password unless you have it stored
via some Git credential helper.

## Installation

pymgit is on PyPi (https://pypi.python.org/pypi/pymgit)

    pip install pymgit

## Command-line Arguments

| Argument | Description | Type | Default Value |
|---|---|---|---|
| `-r`,`--requirements` | The path to the requirements text file containing a list of the Git repos you want to clone | str | no default, this is required |
| `-d`,`--debug` | Turn on more verbose debugging (not much of it really)|bool|false|
| `-v`,`--version` | Display program version | N/A | None |
| `-h`,`--help` | Display program help | N/A | None |

## Dependencies

None

## Examples

### Program Invocation

Run the program to clone all of the repos identified in ~/requirements.yml

    pymgit -r ~/requirements.yml

Run the program and turn on debugging

    pymgit -r ~/requirements.yml -d

Run the program to display the version

    pymgit -v

Run the program with no arguments or the -h/--help option to display help

    pymgit
    pymgit -h

### Requirements File
also see example_requirements.yml

    ---

    - src: git@github.com:watsonb/pymgit.git
      version: develop
      dest: /workspace/foo

    - src: git@github.com:watsonb/pymgit.git
      version: master
      dest: /workspace/bar

Given the above, the program will checkout the pymgit source twice:
- First, the develop branch to the path /workspace/foo
- Second, the master branch to the path /workspace/bar

After running the program with the above example, you should have:
- /workspace/foo/pymgit (checked out to develop)
- /workspace/bar/pymgit (checked out to master)

If these directories already exist and you run the program:
- and the directory **IS** a Git repo --> smiply checks out the version
- and the directory is **NOT** a Git repo --> asks you if you want to delete and clone

This program doesn't do any Git fetching, pushing, pulling (sorry).  Once you
have cloned all of your repos, I highly recommend the NodeJS program `git-run`
to manage the fetching, pushing, pulling, etc. https://www.npmjs.com/package/git-run

## License

MIT

## Contributing

1. Fork it
1. Create your feature branch (`git checkout -b my-new-feature`)
1. Commit your changes (`git commit -am 'Add some feature'`)
1. Push to the branch (`git push origin my-new-feature`)
1. Create new Pull Request

## Building and Distributing

```bash
virtualenv venv_pymgit
source venv_pymgit/bin/activate
pip install GitPython PyYaml
pip twine pyOpenSSL ndg-httpsclient pyasn1
git clone git@github.com:watsonb/pymgit.git
cd pymgit
python setup.py clean
python setup.py check
python setup.py build
python setup.py sdist
twine upload dist/*
```

## Authors

| Author | E-mail | Note |
|---|---|---|
|Ben Watson|bwatson1979@gmail.com|Primary author|
|Derek Halsey| hmd2473@gmail.com | Muse - via his `ansible-sc.py` and `wmachine` programs |