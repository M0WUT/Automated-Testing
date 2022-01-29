from setuptools import find_packages, setup

setup(
    name="AutomatedTesting",
    version="0.0.1",
    url="https://github.com/M0WUT/Automated-Testing.git",
    author="Dan McGraw",
    packages=find_packages(),
    install_requires=[
        "pytest",
        "pytest-cov",
        "pytest-flake8",
        "Xlsxwriter",
        "pyserial",
        "pyvisa",
        "pyvisa-py",
        "numpy",
        "pyusb",
        "GitPython",
    ],
)
