from setuptools import find_packages
from setuptools import setup

setup(
    name='adas_msgs',
    version='1.0.0',
    packages=find_packages(
        include=('adas_msgs', 'adas_msgs.*')),
)
