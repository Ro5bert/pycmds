from setuptools import setup
from version import __version__

setup(
    name='pycmds',
    version=__version__,
    packages=['pycmd'],
    url='https://github.com/Ro5bert/pycmd',
    license='MIT',
    author='Robert Russell',
    author_email='robertrussell.72001@gmail.com',
    description='Wrapper around Click python library',
    install_requires=[
        "click",
        "prompt_toolkit",
    ]
)
