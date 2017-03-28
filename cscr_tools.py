import os
import sys
import site

if sys.platform == 'win32':
    cscr_default='C:\\cscr-tools'
elif sys.platform == 'cygwin':
    cscr_default='/c/cscr-tools'
else:
    cscr_default='/opt/cscr-tools'


cscr_root=os.getenv('CSCR_TOOLS_ROOT')
if cscr_root:
   site.addsitedir(cscr_root + os.sep + 'lib' + os.sep + 'site-packages')
else:
   site.addsitedir(cscr_default + os.sep + 'lib' + os.sep + 'site-packages')
