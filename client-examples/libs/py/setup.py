import setuptools
import menlosystemcore

setuptools.setup(
    name="menlosystemcore",
    version=menlosystemcore.__version__,
    author=menlosystemcore.__author__,
    author_email=menlosystemcore.__email__,
    description="Module for connecting to a remote MenloSystemCore instance",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ),
)
