from setuptools import setup, find_packages

setup(
    name="oks-cli",
    version="1.16",
    packages=['oks_cli'],
    author="Outscale SAS",
    author_email="opensource@outscale.com",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    license="BSD",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    entry_points={"console_scripts": ["oks-cli = oks_cli.main:cli"]},
    install_requires=[
        "certifi>=2024.8.30",
        "charset-normalizer>=3.3.2",
        "click>=8.1.7,<8.3.0",
        "colorama>=0.4.6",
        "idna>=3.10",
        "pyyaml>=6.0.2",
        "requests>=2.32.3",
        "urllib3>=2.2.3",
        "human-readable",
        "prettytable",
        "python-dateutil",
        "altgraph>=0.17.4",
        "pynacl>=1.5.0",
        "pyOpenSSL>=25.0.0"
    ],
    extras_require={
        'dev': [
            'pytest>=8.4.1',
        ],
    }
)
