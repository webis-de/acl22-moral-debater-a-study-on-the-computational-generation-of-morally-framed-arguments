# (C) Copyright IBM Corp. 2020.

import os

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

### collecting all dependencies from re	requirements.txt
thelibFolder = os.path.dirname(os.path.realpath(__file__))
requirementPath = thelibFolder + '/requirements.txt'
install_requires = []
if os.path.isfile(requirementPath):
    with open(requirementPath) as f:
        install_requires = f.read().splitlines()
else:
    raise Exception('error: unable to locate requirements.txt')

setuptools.setup(
    name="debater_python_api",
    version="3.5.8.RELEASE",
    author="Project Debater",
    author_email="amir.menczel@il.ibm.com",
    description="Project Debater API sdk for java and python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.ibm.com/Debater/partners-program",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=install_requires
)
