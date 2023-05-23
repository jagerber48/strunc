from setuptools import setup, find_packages
from pathlib import Path
import re

package = 'strunc'


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
