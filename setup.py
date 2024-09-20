"""
Setup script for the picoDAQ module.

This setup includes the test runner for the module and the setup class for
package information
"""

import sys
from setuptools import setup

pkg_name = "picodaqa"
# import _version_info from package
sys.path[0] = pkg_name
import _version_info

_version = _version_info._get_version_string()


setup(
    name=pkg_name,
    version=_version,
    author='Guenter Quast',
    author_email='Guenter.Quast@online.de',
    packages=[pkg_name],
    install_requires=[],
    scripts=[],
    classifiers=[
    'Development Status :: 5 - Production/Stable',
    # Specify the Python versions you support here.
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
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
