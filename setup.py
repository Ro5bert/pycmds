from setuptools import setup
from version import __version__


with open("README.rst") as readme:
    setup(
        name='pycmds',
        version=__version__,
        packages=['pycmds'],
        url='https://github.com/Ro5bert/pycmds',
        license='MIT',
        author='Robert Russell',
        author_email='robertrussell.72001@gmail.com',
        description='Wrapper around Click python library',
        long_description=readme.read(),
        install_requires=[
            "click",
            "prompt_toolkit",
        ]
    )
