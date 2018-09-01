from setuptools import setup
from version import __version__

setup(
    name='pycmds',
    version=__version__,
    packages=['pycmds'],
    url='https://github.com/Ro5bert/pycmds',
    license='MIT',
    author='Robert Russell',
    author_email='robertrussell.72001@gmail.com',
    description='Wrapper around Click python library',
    install_requires=[
        "click",
        "prompt_toolkit",
    ]
)
