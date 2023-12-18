#!/usr/bin/env python3
import os
from setuptools import setup

dir_path = os.path.dirname(os.path.abspath(__file__))
version = open(os.path.join(dir_path, "VERSION")).read().strip()

def parse_requirements(reqfile):
    r = []
    with open(reqfile, 'r') as f:
        r = f.read().splitlines()
    return r

setup(
    name='aslinuxtester',
    version=version,
    author='Denver Atwood',
    author_email='denver.atwood@abaco.com',
    packages=['aslinuxtester',],
    license='GPLv2',
    description='Controls cobbler and other provisioning tools for Linux testing',
    long_description=open('README.md').read(),
    install_requires=parse_requirements('requirements.txt'),
    tests_require=parse_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'cobblerTool = aslinuxtester.cobbler:main',
            'NFSTool = aslinuxtester.nfs:main',
            'dependenciesTool = aslinuxtester.dependencies:main',
            'testTool = aslinuxtester.test:main',
        ]
    },
)
