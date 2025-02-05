from setuptools import setup, find_packages

setup(
    name="taskbrain",
    version="0.1.1",
    author="Florian BARRE",
    author_email="florian.barre78@gmail.com",
    description="A simple and powerful task scheduler.",
    long_description=open("./ReadMe.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Florian-BARRE/TaskBrain",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    install_requires=[
        "colorama>=0.4.6",
        "contourpy>=1.3.1",
        "cycler>=0.12.1",
        "fonttools>=4.55.8",
        "kiwisolver>=1.4.8",
        "matplotlib>=3.10.0",
        "numpy>=2.2.2",
        "packaging>=24.2",
        "pillow>=11.1.0",
        "pyparsing>=3.2.1",
        "python-dateutil>=2.9.0.post0",
        "six>=1.17.0",
        "loggerplusplus>=0.1.2",
    ],
    include_package_data=True,
)
