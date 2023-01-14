# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from os import path
from shutil import rmtree
import sys

from setuptools import setup

import lstail


NAME = 'lstail'
VERSION = lstail.__version__

here = path.abspath(path. dirname(__file__))
with open(path.join(here, 'README.md'), 'rb') as f:
    LONG_DESCRIPTION = f.read().decode('utf-8')


if 'bdist_wheel' in sys.argv:
    for directory in ('build', 'dist', 'lstail.egg-info'):
        rmtree(directory, ignore_errors=True)  # cleanup


setup(
    name=NAME,
    version=VERSION,
    description='Logstash command line query tool, a bit like tail for Logstash/ElasticSearch',
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    license='MIT',
    author='Enrico Tröger',
    author_email='enrico.troeger@uvena.de',
    url='https://github.com/eht16/lstail/',
    project_urls={
        'Source code': 'https://github.com/eht16/lstail/',
        'Documentation': 'https://lstail.org/',
    },
    keywords='logging logs logstash query tail log-viewer cli',
    python_requires='>=3.9',
    install_requires=['prompt-toolkit'],
    packages=['lstail'],
    include_package_data=True,
    entry_points={
        'console_scripts': ['lstail=lstail.cli:main']
    },
    test_suite='tests',
    classifiers=[
        'Environment :: Console',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: Log Analysis',
        'Topic :: System :: Logging',
    ]
)
