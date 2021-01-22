#built-ins
import os
import sys
import logging
import argparse
import json
import shutil
import fnmatch

#Python3
if sys.version[0] == '3':
    from importlib import reload

#extras
import git  #pip install GitPython
import yaml #pip install PyYaml
from colorama import init #pip install colorama
from termcolor import colored #pip install termcolor

# Python 2/3
# https://python-future.org/compatible_idioms.html
import future        # pip install future
import builtins      # pip install future
import past          # pip install future
import six           # pip install six

# fix the ascii error, from:
# http://mypy.pythonblogs.com/12_mypy/archive/1253_workaround_for_python_bug_ascii_codec_cant_encode_character_uxa0_in_position_111_ordinal_not_in_range128.html
if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding("utf8")

#get the user home directory
user_home = os.environ["HOME"]

# read input parameters
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter,
    description="""
An command-line utility to clone multiple Git repositories to specified paths
and checkout specified version (e.g. branch or tag).

examples:
  Clone all of the repositories specified in the requirements file
    pymgit -r ~/requirements.yml
  Clone all of the repositories specified in the requirements file and debug
    pymgit -r ~/requirements.yml -d
  Clone all of the repositories specified in the requirements file and make 
  a git-run config file in default location
    pymgit -r ~/requirements.yml -g
  Clone all of the repositories specified in the requirements file and force
  existing repositories to checkout tag specified in requirements file 
    pymgit -r ~/requirements.yml -c
  Clone all of the repositories specified in the requirements file and make a git-run
  config in specified location
    pymgit -r ~/requirements.yml -g -p /some/path/user/can/write
    
""")

# going to create our own groups so they show up in correct order in help
parser._action_groups.pop()
required = parser.add_argument_group('required arguments')
optional = parser.add_argument_group('optional arguments')

# required arguments
required.add_argument('-r', '--requirements',
                      help='Path to requirements file containing list of repos.\n  example: ~/requirements.yml',
                      required = True)

#optional arguments
#TODO: always update VERSION number, it is right -------------------------->HERE!<
optional.add_argument('-v', '--version', action='version', version='pymgit v0.6.0 Squirtle')
optional.add_argument('-c', '--checkout', action='store_true',
                      help='Force existing repos to checkout tag in requirements file')
optional.add_argument('-d', '--debug', action='store_true', help='Turn on debugging (verbose) output')
optional.add_argument('-g', '--gitrun', action='store_true',
                      help='Do produce a git-run manifest/tag file (.grconfig.json)')
optional.add_argument('-p', '--gitrunconfigdir',
                      help='Which directory to write the .grconfig.json file.  Defaults to your home directory.',
                      default=user_home)
optional.add_argument('-s', '--strip', action='store_true',
                      help='DANGER: THERE BE DRAGONS HERE. Strips .git directory (and other related git files) \
                      from existing and cloned repositories')
optional.add_argument('-f', '--force', action='store_true',
                      help='DANGER: THERE BE DRAGONS HERE. Will force pymgit to always overwrite existing directories.')
optional.add_argument('-S', '--donotstripreadme', action='store_true',
                      help="Don't strip the README.md file")

args = parser.parse_args()

requirements = args.requirements
debug = args.debug
do_gr = args.gitrun
do_checkout = args.checkout
do_force = args.force
do_strip = args.strip
do_not_strip_readme = args.donotstripreadme
gitrunconfigpath = os.path.join(args.gitrunconfigdir, '.grconfig.json')

strip_list = [
    '.git*',
    '*.md',
    '.yamllint',
    '.ansible-lint',
]

if do_gr:
    gr_config_dict = {}
    gr_config_dict['tags'] = {}

if debug:
    # explicitly setup logging for enhanced GitPython output
    logging.basicConfig(level=logging.DEBUG)
    os.environ["GIT_PYTHON_TRACE"] = "full"
    print(os.environ["GIT_PYTHON_TRACE"])
    print (gitrunconfigpath)
else:
    # explicitly setup logging for enhanced GitPython output
    logging.basicConfig(level=logging.ERROR)
    try:
        os.environ.pop("GIT_PYTHON_TRACE")
    except:
        pass

# use Colorama to make Termcolor work with Windows
init()

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
        print(colored("checked out ", 'white', attrs=['bold']) + colored(version, 'cyan', attrs=['bold']))
    except git.exc.GitCommandError:
        print(colored("there is no branch/tag named " + version, 'red', attrs=['bold']))

def clone_and_checkout(src, path, version):
    """
    Clone a Git repo and checkout a branch/tag

    :param src: The source of the Git repo
    :param path: The path to clone into
    :param version: The branch/tag to checkout
    :return: None
    """

    for attempt in range(3):
        try:
            git.Repo.clone_from(src, path)
            print (colored("cloned ", 'white', attrs=['bold']) + colored(src, 'green', attrs=['bold']))
            checkout(path, version)
        except:
            print (colored("error cloning " + src + " trying again", 'yellow', attrs=['bold']))
        else:
            break
    else:
        print (colored("error cloning " + src + " moving on", 'red', attrs=['bold']))

class Repo(object):
    def __init__(self, src, dest, version, tags=[], name=None):
        """
        A Git repository information object

        :param src: The source of the Git repository to clone
        :param dest: The destination on the file system to place the clone
        :param version: The branch/tag to checkout
        :param tags: A list of git-run tags
        """

        self.src = src
        self.version = version
        self.tags = tags
        if name is None:
            self.dest = dest
        else:
            self.dest = dest + '/' + name
        self.name = name

class Repos(object):
    def __init__( self, path ):
        """
        A Git requirements information object

        :param path: The path to the requirements file
        """
        self.path = path
        self.repoList = []

def add_tag_to_dict(tag, path):
    """
    Add a git-run tag to a dictionary to generate the .grconfig.json file

    :param tag: the tage to add (str)
    :param path: the path to the git repo associated with the tag (str)
    :return: None
    """
    if tag in gr_config_dict['tags']:
        gr_config_dict['tags'][tag].append(path)
    else:
        gr_config_dict['tags'][tag] = []
        gr_config_dict['tags'][tag].append(path)


def main():

    if do_gr and do_strip:
        print ("It doesn't make sense to produce a git-run manifest and strip .git files from your repos")
        sys.exit()

    #instantiate Repos object with path to requirements YAML file
    repos = Repos(requirements)
    if debug:
        print (colored(repos.path, 'grey', 'on_white'))

    if do_force:
        print ('Force Mode Enabled')

    if do_strip:
        print ('Strip Mode Enabled')

    # open the YAML file
    stream = open(repos.path , 'r')

    # assign the yaml list to a list
    # see https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation
    reqs = yaml.load(stream, Loader=yaml.FullLoader)

    for req in reqs:

        if do_gr:
            try:
                repo = Repo(req['src'], req['dest'], req['version'], req['tags'], name=req['name'])
            except:
                repo = Repo(req['src'], req['dest'], req['version'], req['tags'])
        else:
            try:
                repo = Repo(req['src'], req['dest'], req['version'], name=req['name'])
            except:
                repo = Repo(req['src'], req['dest'], req['version'])

        if debug:
            if do_gr:
                print (colored("repo.src = " + repo.src \
                               + " repo.dest = " + repo.dest \
                               + " repo.version = " + repo.version\
                               + " repo.tags = " + ' '.join(repo.tags), 'grey', 'on_white'))
            else:
                print (colored("repo.src = " + repo.src \
                               + " repo.dest = " + repo.dest \
                               + " repo.version = " + repo.version \
                               ,'grey', 'on_white'))

        repos.repoList.append(repo)

    for r in repos.repoList:

        if r.name is None:
            repoName = r.src.split('/')[-1].split('.')[0]
            repoPath = os.path.join(r.dest, repoName)
        else:
            repoPath = r.dest

        seperator = '/'
        repoDir = seperator.join(repoPath.split('/')[:-1])

        if do_gr:
            for tag in r.tags:
                add_tag_to_dict(tag, repoPath)

        if not os.path.exists( repoDir):
            if debug:
                print (colored(repoDir + " does not exist, creating...", 'grey', 'on_white'))
            os.makedirs(repoDir)

        if do_force:
            print (colored("Removing: " + repoPath, 'yellow', attrs=['bold']))
            shutil.rmtree(repoPath, ignore_errors=True)

        if os.path.exists(repoPath):
            if is_git_repo( repoPath ):
                print (colored(repoPath, 'green', attrs=['bold']) + \
                       colored(" already exists and is a Git repository", 'white'))
                if do_checkout:
                    checkout(repoPath, r.version)
                print ('')
            else:
                print (colored(repoPath + " already exists and is NOT a Git repository", 'magenta', attrs=['bold']))
                if yes_or_no("Shall I delete this directory and clone to it? (y/n): "):
                    print (colored("Deleting " + repoPath, 'white', attrs=['bold']))
                    shutil.rmtree(repoPath)
                    clone_and_checkout(r.src, repoPath, r.version)
                    print ('')
                else:
                    print (colored("OK, skipping this one...", 'green', attrs=['bold']))
        else:
            clone_and_checkout(r.src, repoPath, r.version)
            print ('')

        if do_strip:
             for pattern in strip_list:
                 for root, dirnames, filenames in os.walk(repoPath):

                     for dirname in fnmatch.filter(dirnames, pattern):
                        print ("removing " + os.path.join(root, dirname))
                        shutil.rmtree(os.path.join(root, dirname), ignore_errors=True)

                     for filename in fnmatch.filter(filenames, pattern):
                         if filename == 'README.md':
                            pass
                         else:
                            print ("removing " + os.path.join(root, filename))
                            os.remove(os.path.join(root, filename))

    if do_gr:
        with open(gitrunconfigpath,'w') as outfile:
            json.dump(gr_config_dict, outfile, indent=4)

if __name__ == "__main__":
    main()