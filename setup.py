from setuptools import setup

with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

setup(
    name = "matview",
    version = "0.0.1",
    packages=["matview"],
    install_requires=install_requires
)

