from setuptools import setup, find_packages


with open("requirements.txt") as f:
    requirements = f.read().splitlines()


setup(
    name="dash",
    version="0.0.1",
    description="DASH video downloader from video-sharing server Vimeo.com",
    author="Martin Bečka",
    author_email="becka.martin@icloud.com",
    packages=find_packages(),
    install_requires=requirements,
)