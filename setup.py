import os
import pathlib

import pkg_resources
from setuptools import find_packages, setup

BASEDIR = os.path.dirname(os.path.abspath(__file__))


def parse_reqs(reqs_file):
    """parse the requirements"""
    install_reqs = list()
    with pathlib.Path(reqs_file).open() as requirements_txt:
        install_reqs = [
            str(requirement) for requirement in pkg_resources.parse_requirements(requirements_txt)
        ]
    return install_reqs


requirements = parse_reqs(os.path.join(BASEDIR, "requirements.txt"))

setup(
    name="vsm",
    version="0.1.0",
    description="Visualization SBO Middleware",
    author="Pawel Podhajski",
    author_email="pawel.podhajski@epfl.ch",
    license="MIT",
    packages=find_packages(),
    zip_safe=False,
    install_requires=requirements,
    entry_points={
        "console_scripts": ["ws_proxy=vsm.slave:main", "mooc_proxy=vsm.master:main"],
    },
)
