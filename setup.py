from setuptools import setup, find_packages

setup(
    name="Katamari",
    version="0.1.0",
    description="Katamari Ecosystem - Real-time, event-driven platform",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Gregory Disney-Leugers",
    author_email="your.email@example.com",
    url="https://github.com/gddisney/Katamari",
    include_package_data=True,
    packages=find_packages(include=["KatamariSDK*"]),  # Updated to match the KatamariSDK name
    install_requires=[
        # Core dependencies based on provided imports
        "fastapi",
        "openai",
        "boto3",
        "azure-mgmt-compute",
        "azure-identity",
        "azure-mgmt-storage",
        "pyyaml",
        "aiofiles",
        "matplotlib",
        "orjson",
        "cachetools",
        "whoosh",
        "fido2",
        "google-cloud-storage",
        "google-cloud-compute",
        "portalocker",
        "zstandard",
        "PyJWT",
        "argon2-cffi",
        "cryptography",
        "requests",
        "dateutil",
        "websockets"
    ],
    python_requires=">=3.11",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "katamari-cli=KatamariSDK.KatamariCLI:main",  # Update to match the new KatamariSDK name
        ]
    },
)

