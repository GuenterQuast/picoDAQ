import picodaqa  # from this directory
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand

# class for running unit tests
# from: https://pytest.org/latest/goodpractices.html
class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.pytest_args)
        sys.exit(errcode)

setup(
    name='picodaqa',
    version=picodaqa.__version__,
    author='Guenter Quast',
    author_email='Guenter.Quast@online.de',
    packages=['picodaqa'],
    install_requires=[],
    scripts=[],
    classifiers=[
    'Development Status :: 5 - Production/Stable',
    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    ],
    url='https://www.etp.kit.edu/~quast/',
    license='GNU Public Licence',
    description='Data AcQuisition and analysis with PicoScope usb-oscilloscopes',
    long_description=open('README.md').read(),
    setup_requires=[\
        "picoscope",            
        "NumPy >= 1.16.2",
        "SciPy >= 1.1.0",
        "matplotlib >= 3.0.0",]
)
