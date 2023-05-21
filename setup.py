from setuptools import setup, find_packages
from pathlib import Path
import sys
import re

package = 'strunc'


def forbid_publish():
    """ Prevent users of setup.py from possibly publishing to PyPI.
    """
    # 'testarg' is for testing this command
    blacklist = ['register', 'upload', 'upload_docs', 'testarg']

    for command in blacklist:
        if command in sys.argv:
            err_str = ('The input command \'{command}\' has been '
                       'blacklisted, exiting...')
            raise RuntimeError(err_str)


# This command must run before anything else in this file!
forbid_publish()


def extract_version():
    with open(Path(Path.cwd(), package, '__init__.py')) as fi:
        for line in fi:
            match = re.search(r'(\d+\.\d+\.\d+)', line)
            if match:
                return match.group(1)
    raise Exception(f'Unable to find {package} version number!')


setup(
    name=package,
    packages=find_packages(),
    description=('Format value/uncertainty pairs into scientific '
                 'notations'),
    version=extract_version(),
    author='Justin Gerber'
)
