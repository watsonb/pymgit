import os
import sys
import git
import urllib
import yaml
import shutil
import argparse

# fix the ascii error, from:
# http://mypy.pythonblogs.com/12_mypy/archive/1253_workaround_for_python_bug_ascii_codec_cant_encode_character_uxa0_in_position_111_ordinal_not_in_range128.html
reload(sys)
sys.setdefaultencoding("utf8")

# read input parameters
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter,
    description="""
An command-line utility to clone multiple Git repositories to specified paths
and checkout specified version (e.g. branch or tag).

examples:
  Clone all of the repositories specified in the requirements file
    pymgit -r ~/requirements.yml
    
""")

# going to create our own groups so they show up in correct order in help
parser._action_groups.pop()
required = parser.add_argument_group('required arguments')
optional = parser.add_argument_group('optional arguments')

# required arguments
required.add_argument('-r', '--requirements', help='Path to requirements file containing list of repos.\n  example: ~/requirements.yml', required = True)

#optional arguments
optional.add_argument('-v', '--version', action='version', version='pymgit v0.1.0')
optional.add_argument('-d', '--debug', action='store_true', help='Turn on debugging (verbose) output')

args = parser.parse_args()

requirements = args.requirements
debug = args.debug

def is_git_repo(path):
    """
    Determine if given path is a Git repository

    :param path: the path to a potential Git repo
    :return: True if it is a Git repository, otherwise False
    """
    try:
        _ = git.Repo(path).git_dir
        return True
    except git.exc.InvalidGitRepositoryError:
        return False

def git_tag_exists(repo, tag):
    """
    Determine if a given repo has a given tag or branch to checkout

    :param repo: a Git repository
    :param tag: The name of a tag or branch to checkout
    :return: True if the repository has a tag/branch, otherwise False
    """
    try:
        repo.checkout(tag)
        return True
    except git.exc.GitCommandError:
        return False

def yes_or_no(question):
    """
    Ask the user a question and expect a yes (y) or no (n) answer

    :param question: A question to the end user
    :return: True if the user answers 'y', False if the user answers 'n'
    """
    while "the answer is invalid":
        reply = str(raw_input(question+' (y/n): ')).lower().strip()
        if reply[:1] == 'y':
            return True
        if reply[:1] == 'n':
            return False

def checkout(path, version):
    """
    Checkout a branch/tag

    :param path: the path to the Git repo
    :param version: the branch/tag to checkout
    :return: None
    """
    repo = git.Git(path)
    try:
        repo.checkout(version)
        print("checked out " + version)
    except git.exc.GitCommandError:
        print("there is no branch/tag named " + version)

def clone_and_checkout(src, path, version):
    """
    Clone a Git repo and checkout a branch/tag

    :param src: The source of the Git repo
    :param path: The path to clone into
    :param version: The branch/tag to checkout
    :return: None
    """
    try:
        git.Repo.clone_from(src, path)
        print ("cloned " + src)
        checkout(path, version)
    except git.exc.GitCommandError:
        print ("error cloning " + src)

class Repo(object):
    def __init__( self, src, dest, version ):
        """
        A Git repository information object

        :param src: The source of the Git repository to clone
        :param dest: The destination on the file system to place the clone
        :param version: The branch/tag to checkout
        """
        self.src = src
        self.dest = dest
        self.version = version

class Repos(object):
    def __init__( self, path ):
        """
        A Git requirements information object

        :param path: The path to the requirements file
        """
        self.path = path
        self.repoList = []

def main():

    #instantiate Repos object with path to requirements YAML file
    repos = Repos(requirements)
    if debug:
        print ( repos.path )

    # open the YAML file
    stream = open( repos.path , 'r')

    #assign the yaml list to a list
    reqs = yaml.load( stream )

    for req in reqs:

        repo = Repo(req['src'], req['dest'], req['version'])

        if debug:
            print ("repo.src = " + repo.src + " repo.dest = " + repo.dest + " repo.version = " + repo.version)

        repos.repoList.append(repo)

    for r in repos.repoList:
        repoName = r.src.split('/')[-1].split('.')[0]
        repoPath = os.path.join(r.dest, repoName)

        if not os.path.exists( r.dest ):
            if debug:
                print (r.dest + " does not exist, creating...")
            os.makedirs(r.dest)

        if os.path.exists(repoPath):
            if is_git_repo( repoPath ):
                print (repoPath + " already exists and is a Git repository")
                checkout(repoPath, r.version)
                print ('')
            else:
                print (repoPath + " already exists and is NOT a Git repository")
                if yes_or_no("Shall I delete this directory and clone to it? (y/n): "):
                    print ("Deleting " + repoPath)
                    shutil.rmtree(repoPath)
                    clone_and_checkout(r.src, repoPath, r.version)
                    print ('')
                else:
                    print ("OK, skipping this one...")
        else:
            clone_and_checkout(r.src, repoPath, r.version)
            print ('')

if __name__ == "__main__":
    main()