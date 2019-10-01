#!/usr/bin/env python3

from setuptools import setup
from setuptools import find_packages


setup(
    name="oors",
    version="0.1",
    description="Driver for opticlock ORS",
    long_description=open("README.md").read(),
    author="Robert Jördens",
    author_email="rj@quartiq.de",
    url="https://github.com/quartiq/oors",
    download_url="https://github.com/quartiq/oors",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "aqctl_oors = oors.aqctl_oors:main",
        ],
    },
    test_suite="oors.test",
    license="LGPLv3+",
)
