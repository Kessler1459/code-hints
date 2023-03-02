from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="code-hints",
    version="0.1.0",
    description="A python file parser with a web API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Kessler1459/code-hints",
    author_email="kessler1459@gmail.com",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "mpi4py>=2.0",
        "numpy",
        "anyio==3.6.2",
        "beautifulsoup4==4.11.2",
        "boto3==1.26.72",
        "botocore==1.29.72",
        "certifi==2022.12.7",
        "charset-normalizer==3.0.1",
        "click==8.1.3",
        "colorama==0.4.6",
        "fastapi==0.92.0",
        "h11==0.14.0",
        "httptools==0.5.0",
        "idna==3.4",
        "jmespath==1.0.1",
        "lxml==4.9.2",
        "pydantic==1.10.5",
        "python-dateutil==2.8.2",
        "python-dotenv==0.21.1",
        "PyYAML==6.0",
        "requests==2.28.2",
        "s3transfer==0.6.0",
        "six==1.16.0",
        "sniffio==1.3.0",
        "soupsieve==2.4",
        "starlette==0.25.0",
        "typing_extensions==4.5.0",
        "urllib3==1.26.14",
        "uvicorn==0.20.0",
        "watchfiles==0.18.1",
        "websockets==10.4"
    ],
    classifiers=[
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
