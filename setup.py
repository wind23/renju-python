from distutils.core import setup

from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name='renju',
    packages=['renju'],
    version='0.0.1',
    license='MIT',
    description='A simple library for the game board of renju.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tianyi Hao',
    author_email='haotianyi0@126.com',
    url='https://github.com/wind23/renju-python',
    download_url='https://github.com/wind23/renju-python/archive/0.0.1.tar.gz',
    keywords=['renju'],
    install_requires=[],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)