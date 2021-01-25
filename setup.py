from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="LogStacker",
    version="0.0.0",
    author="Ron Chang",
    author_email="ron.hsien.chang@gmail.com",
    description="A colourful and less settings logger, based on built-in package `logging`.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ron-Chang/LogStacker",
    packages=find_packages(),
    license='MIT',
    python_requires='>=3.6',
    exclude_package_date={'':['.gitignore', 'setup.py']},
    install_requires=[]
)
