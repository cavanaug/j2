# Note:  
#    This is a bit of a hack to make things work properly on windows with bin.
#    However it still doesnt quite do the right thing in terms of dropping the .py on unix platforms, sigh...
#

from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
import os, sys

required_python_version = '3.6'


def main():
    if sys.version < required_python_version:
       print("Requires Python %s or later" % (required_python_version))

    # Force scripts into bin even on windows
    for scheme in INSTALL_SCHEMES.values():
       scheme['scripts']='$base/bin'


    dist=setup(name='j2',
               version='2.2',
               scripts = ['j2.py'],
              )

if __name__ == "__main__":
   main()

