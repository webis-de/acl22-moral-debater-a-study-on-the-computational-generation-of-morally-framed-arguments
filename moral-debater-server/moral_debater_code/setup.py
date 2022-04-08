# (C) Copyright IBM Corp. 2020.

import os

import setuptools

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
    name="moral_debater",
    version="1.0.0",
    author="Milad Alshomary",
    author_email="milad.alshomary@gmail.com",
    description="Moral Debater",
    url="https://github.com/MiladAlshomary/moral-debater",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.6',
    install_requires=install_requires,
    package_data={'': ['*.ini']}
)
