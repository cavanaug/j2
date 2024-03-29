#!/usr/bin/env python3

# Author: John Cavanaugh (cavanaug@hp.com)

#
# Simple Jinja2 cmdline helper to facilitate template expansion
#

#
# ChangeLog
# ========= 
#
#     0.7 - Internal beta version
#         * Single files only 
#         * Support both dos & unix
#
#     1.0 - Initial public version
#         * Add j2 internal variables
#         * Better docs & more examples
#
#     2.0 - Mo Betta Features
#         * Add recursive folder processing
#         * Renaming support within folders
#         * Better docs & more examples
#
#     2.1 - Cleanups & minor feature
#         * Add hidden (for now) -M feature
#     2.2 - Unicode support
#         * Add hidden (for now) -M feature
#     2.3 - Cleanup & minor fixes
#         * Line-encoding agnostic
#     2.4 - Cleanup & minor fixes
#         * Add support for template search path
#         * More pep8 compliant

import argparse
import os
import sys
import traceback
import re
import datetime
import getpass
import socket
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateError, TemplateNotFound, TemplateSyntaxError
#import codecs

#
# Key Configuration Items
#
j2 = { 'versionnum' : 2.4 }
ignoredirs = set(['.git', '.hg', '.svn'])
j2_encoding = 'utf-8'
j2_linesep = os.linesep


#
# Documentation
#    - I like to keep everything all in one file for utility tools like this
#
class InfoAction(argparse.Action):
    def __call__ (self, parser, namespace, values, option_string=None):
        #print '%r %r %r' % (namespace, values, option_string)
        header ="""
    NAME
           j2 - Jinja2 commandline template processor
    
    
    SYNOPSIS
           j2 [options] [-m module] template.j2t
    
           Render the file template.j2t to STDOUT
    
    
    DESCRIPTION
           Jinja2 is a very capable templating system used throughout the Python community. Its 
           features & capabilities are extensive & robust.  However to access, one typically writes
           a python application or script and programatically loads & renders templates.  
    
           j2 makes this Jinja2 templating available on the command line.   Using an MVC metaphor,
           think of the python file foo.py (module foo) as the (M)odel, a template file template.j2t 
           as the (View) and the commandline j2 interface as the (C)ontroller.
    
           Template files (usually suffixed with j2t) are simply normal Jinja2 templates.   The
           format of these files is extensively documented at the Jinja2 project homepage. 
    
           Modules are just a fancy word for py files.  They provide the mechanism to load the
           context that is used in rendering the template.   All modules are loaded into the
           global namespace via an exec of "from module import *".  The entire global namespace 
           is then made available in the templates for rendering. 
    
           The combination of templates and flexible module loading makes j2 a very useful tool
           in code generation or any other general purpose cmdline template processing.   We
           have been using j2 successfully in our build environment similarly to a compiler
           for rendering templates into output files.
    
           Despite the fact I dont think this will ever be a real issue for usage, I am a bit
           of a security nut, so folks should be aware that the way j2 works by executing 
           arbitrary modules, it could be used do damage to a system.  So basically dont use j2 
           in environments where you cant trust the modules or templates.
    
    
    OPTIONS
    
    """
        trailer = """
    
    EXAMPLES
    
           EXAMPLE #1 - Simple File Template

           Here is a simple template that when rendered will output all your current environment
           variables to STDOUT.   While a trivial example and something that could just as easily
           be done with a python script, this demonstrates how the normal python global context is 
           always available in templates.
       
           user> cat environment.j2t
           {% for item in os.environ %}
           {{ item }} = {{ env[item] }}
           {% endfor %}
       
           user> j2 environment.j2t
           SSH_AGENT_PID = 6052
           LANG = en_US
           INFOPATH = /usr/local/info:/usr/share/info:/usr/info:
           TERM = xterm-256color
           SHELL = /bin/bash
           ...


           EXAMPLE #2 - cmdline expressions and shell quoting

           Another example this time utilizing the cmdline expression syntax for passing variables
           to templates & modules.   In our organization we use j2 on both Linux & Windows, and
           it performs fine, but you need to be aware of the differences in cmdline calling
           conventions.  

           user> cat passed.j2t
           This is a sample template that can be called like

           Unix:  j2.py -e'string="with spaces"' -eword="singular" -enumber=23 passed.j2t
            DOS:  j2.py -e"string='with spaces'" -e"word=singular" -enumber=23 passed.j2t

            string = {{ string }}
            word = {{ word }}
            number = {{ number }}


           Notice the slight syntax changes required to pass strings with spaces on Unix
           vs Dos.   While this can be infuriating for folks working on both platforms, it
           is something that is a limitation of the DOS vs UNIX shells.


           EXAMPLE #3 - More Window'isms...

           One issue folks on DOS often have is how to properly escape file paths such 
           as C:\\build

           In this scenario the \\b will get expanded to a <backspace> character, with the path
           showing as C:build.  When this occurs, novice users are often very confused as to
           what happened.  The problem & the answer is hidden in how python processes strings.

           Normally \\ characters are expanded to allow for access special characters (similiar
           to printf).   Prefixing a python with r' removes the typical expansion of \\ characters.

           dos_user>  j2 -efoo=r'C:\\Build' -ebar=23 passed.j2t


           EXAMPLE #4 - J2 Internal Variables

           J2 has a number of internal variables that are intended to help the template designer 
           create robust & informative template renderings.

           Here is a quick sample of the internals made available.

           unix> cat examples/internals.j2t
           This is a sample template to show the current internal j2 variables

           j2.py internals.j2t

           {% for item in j2|sort %}
           j2.{{ item }} = '{{ j2[item] }}'
           {% endfor %}

           unix> j2.py examples/internals.j2t 
           This is a sample template to show the internal j2 variables

           j2.py internals.j2t

           j2.date = '05/27/2011'
           j2.expressions = 'None'
           j2.log = 'J2: Template /m/f_drive_ssd/src_hp/cscr-tools.trunk/src/python/j2/folder_example.j2t/internals'
           j2.log1 = '    processed on 05/27/2011 at 11:17 PM'
           j2.log2 = '    using modules None'
           j2.log3 = '    with expressions None'
           j2.modules = 'None'
           j2.templatepath = '/m/f_drive_ssd/src_hp/cscr-tools.trunk/src/python/j2/folder_example.j2t/internals'
           j2.time = '11:17 PM'
           j2.version = 'J2 Version 2.0'
           j2.versionnum = '2.0'
           j2.warning = 'WARNING!! DO NOT EDIT THIS FILE, ALL CHANGES WILL BE LOST. THIS FILE IS AUTOGENERATED BY J2.'


           EXAMPLE #5 - Template Best Practices

           Creating trackable rendered templates is a best practive for any system extensively using
           J2.  Using J2 internals judiciously in comment fields makes it easy to know where things 
           came from and to avoid any mixups with people editing autogenerated files.


           unix> cat examples/environ.xml.j2t
           <?xml version="1.0" encoding="ISO-8859-15"?>
           <!--
             {{j2.warning}}
             {{j2.warning}}
           -->
           
           <!--
           This is a sample template showing how to have templates that still conform
           to an XML schema.   Basically you encapsulate jinja constructs inside of
           xml comments.  Also note how env[item] is filtered (using |e) using the escape 
           module to prevent invalid xml from being generated if values contain < & or >
           -->
           
           <!--
             {{j2.log}}
             {{j2.log1}}
             {{j2.log2}}
             {{j2.log3}}
           -->
           
           <variables>
           <!-- {% for item in os.environ|sort -%} -->
            <variable>
              <name>{{ item }}</name>
              <value>{{ env[item]|e }}</value>
            </variable>
           <!-- {% endfor -%} -->
           </environment>


           Below shows what that template looks like after rendering.   
             *  Notice the prominent notice regarding autogeneration.
             *  Notice how the both the template & output was valid xml 
             *  Notice the J2 log information

           unix> j2.py examples/environ.xml.j2t  
           <?xml version="1.0" encoding="ISO-8859-15"?>
           <!--
             WARNING!! DO NOT EDIT THIS FILE, ALL CHANGES WILL BE LOST. THIS FILE IS AUTOGENERATED BY J2.
             WARNING!! DO NOT EDIT THIS FILE, ALL CHANGES WILL BE LOST. THIS FILE IS AUTOGENERATED BY J2.
           -->
           
           <!--
           This is a sample template showing how to have templates that still conform
           to an XML schema.   Basically you encapsulate jinja constructs inside of
           xml comments.  Also note how env[item] is filtered using the escape module
           to prevent invalid xml from happening if values contain < & or >
           
              j2.py environment.xml.j2t
           -->
           
           <!--
             J2: Template /src_hp/cscr-tools.trunk/src/python/j2/examples/environ.xml.j2t
                 processed on 05/27/2011 at 11:32 PM
                 using modules None
                 with expressions None
           -->
           
          ... <output truncated for brevity>



           EXAMPLE #6 - Folder Templates

           An advanced usage of j2 moves beyond just a single file template.  With folder templates 
           you can utilize a folder tree of templates to create an entire project structure.

           unix> ls folder_example.j2t/
           ./  ../  environ.xml  internals  passed
           unix> j2.py --folder folder_example.j2t -o bar
           cavanaug@jc-8740w:~/src_hp/cscr-tools.trunk/src/python/j2$ ls bar
           ./  ../  environ.xml  internals  passed

           You can see here that all of the templates in the folder_example.j2t folder have been 
           processed creating rendered files in folder bar.  This folder expansion is done 
           recurisvely so the structure could be as many levels deep as needed.


           EXAMPLE #7 - Advanced Folder Templates

           In the previous example it was shown how to utilize the power of Folder Templates to 
           create full hierarchies from templates.  Typical usage for Folder Templates has been
           to create a full project structure to match a standard, often utilized in designs
           that focus on convention over configuration.

           A problem often faced with these structures is how do you handle situations where you 
           need customization of the rendered template filenames and/or subdirectory names.   

           Up to this point in all of the documentation we have only discussed how to render 
           the contents of the files not the file or directory names.

           To allow for the customization of file & directory names in Folder Templates J2 uses 
           a specially named template file which when rendered will be used as the file or 
           directory name.   

           unix> ls folder_example2.j2t/
           ./  ../  internals  internals.j2n
           unix> cat folder_example2.j2t/internals.j2n
           {{ prefix }}-internals

           In essence, after rendering the internals template file, it will be renamed to whatever 
           the rendered output of internals.j2n (Jinja2 Namefile) is.

           unix> j2.py -e'prefix="sampleproject"' --folder folder_example2.j2t -o foo
           unix> ls folder_example2.j2t/
           ./  ../  sampleproject-internals


           EXAMPLE #8 - Unicode & J2

           Unicode is natively supported by Jinja2 and can be used by j2.   The default encoding
           for all templates and outputs is utf-8.   To change this you need to change the
           j2_encoding variable on the cmdline.

           unix> j2.py -e"j2_encoding='utf-16'" examples/utf16_example.j2t  

           There is a limitation with encoding in that it is a global setting, which means you
           can not use folder templates which has files that have different encodings.

           For folks wanting to understand what encoding was used when a template was rendered
           there is an internal variable available that shows the encoding used {{j2.encoding}}



    DESIGN TRADEOFFS
    
           Developing J2 was not without some soul searching as to what it should become and
           more importantly how things should work from the users perspective.  I strived to
           make it as simple to use from the cmdline as possible, with the least amount of
           complexity required, while still providing powerful capabilities.
           
           Two items stand out as key design decisions.

           Folder Templates while a powerful feature added a fair amount of complexity & code
           to J2.   The tool was in usage for several months before this feature was added,
           thus far for the situations it has been used in, this feature has proven to be *very*
           useful in eliminating multiple calls to j2 for each file.

           File & Directory naming as part of Advanced Folder Templates was another feature that 
           was difficult to find the *best* way to support.   Several different options were 
           considered, including:  a rendered _j2.py file that would rename files which would be 
           eval'd, a rendered _j2.py that build a datastructure which would be used to rename 
           files, a rendered j2.json file that would be read in and used to rename files.   In 
           the end I went with the .j2n model primarily to avoid having to expect the template 
           author to know python and instead have them only rely on the Jinja2 language they
           already know.


    
    SEE ALSO
    
           Jinja2 Template Designer Docs - http://jinja.pocoo.org/docs/templates/
           Jinja2 Website - http://http://jinja.pocoo.org/
           Jinja2 Github - http://github.com/mitsuhiko/jinja2

           simplejson Python Module - http://pypi.python.org/pypi/simplejson/
           xmlbegone Python Module - http://pypi.python.org/pypi/xmlbegone


    
    """
        print(header)
        print( "       " + re.sub('\n', "\n       ", parser.format_help(), count=0))
        print(trailer)
        exit(0)

#
# TODO: This debugging routine should be refactored out into a standard logging class
#
DEBUG_LEVEL = 0
def DEBUG(level, output):
    if DEBUG_LEVEL >= level: 
        sys.stderr.write('DEBUG('+str(level)+') '+output+os.linesep)


#
# cmdline argument processing
#
parser = argparse.ArgumentParser("j2")
parser.add_argument('template', nargs='+', help='template to render')
parser.add_argument('--info', nargs=0, action=InfoAction, help='show the manpage and exit')
parser.add_argument('-o', dest='OUTPUT', default=":NONE:",
                    help='output location (Default is STDOUT for file and PWD for folder)')
parser.add_argument('-F', '--folder', dest="FOLDER", action='store_true',
                    help='process folder of templates recursively')
parser.add_argument('-P', '--template-path', dest="TEMPLATEPATH", action="append",
                    help='Add paths to search for included or nested templates when rendering')
parser.add_argument('-I', dest="INCLUDE", action="append",
                    help='add path to the search list for module imports')
parser.add_argument('-m', '--module', dest="MODULE", action="append",
                    help='load module(s) via import prior to template rendering, this allows for creating rendering context')
parser.add_argument('-M', '--module-fullpath', dest="MODULEPATH", action="append",
                    help='load module(s) via exec prior to template rendering, this allows for creating rendering context')
parser.add_argument('-e', dest="EXPR", action="append",
                    help='evaluate expression prior to module loading, this allows for usage of vars in modules')
parser.add_argument('-t', '--trim-mode', dest="TRIM", type=int, default=1,
                    help='set Jinja2 trim mode (Default is 1)')
parser.add_argument('-d', '--debug', action='count', dest="DEBUG", default=0,
                    help='output debug information to stderr')
parser.add_argument('--version', action='version', version=j2['versionnum'],
                    help='show the version and exit')
args=parser.parse_args()


#from pudb import set_trace; set_trace()

#
# Main Application begins here
#
if args.DEBUG:
    DEBUG_LEVEL = args.DEBUG


if args.INCLUDE:
    for include in args.INCLUDE:
        DEBUG(1, "Adding directory '" + include + "' to module search path")
        sys.path.append(include)

if args.EXPR:
    for expr in args.EXPR:
        DEBUG(1, "Evaluating expression '" + expr + "'")
        exec(expr)


# The module processing here is rather sub-optimal.   I would prefer to use the import module but 
# that is not available until Python 3.   This was the best compromise I could come up with.
if args.MODULE:
    for modname in args.MODULE:
        DEBUG(1, "Loading module " + modname)
        for path in sys.path:
            pyfile = path + os.sep + modname + ".py"
            DEBUG(2, "  Trying " + pyfile)
            try:
                if os.path.exists(pyfile):
                    DEBUG(2, "  Found module " + modname + " at " + pyfile + os.linesep)
                    execfile(pyfile)
                    break
            except Exception as e:
                sys.stderr.write("j2: Command line error ImportUnk: Module " + modname + ', ' + str(e) + os.linesep)
                if DEBUG_LEVEL > 0:
                    traceback.print_exc()
                exit(1)
        else:
            sys.stderr.write("j2: Command line error ImportError: Can't find module " + modname + ' for importing' + os.linesep)
            exit(1)


# While we still encourage the use of models in well established folders for reuse, some have wanted a simple
# way to specify the path to a single python file as a module.   We dont recommend using BOTH -m & -M on the
# same cmdline call.    This feature may get removed/refactored at a later date as its a bit ugly.
if args.MODULEPATH:
    for modpath in args.MODULEPATH:
        DEBUG(1, "Loading module from location " + modpath)
        try:
            if os.path.exists(modpath):
                DEBUG(2, "  Found module " + modpath + os.linesep)
                execfile(modpath)
                break
            else:
                sys.stderr.write("j2: Command line error ImportError: Can't find module at location " + modpath + ' for importing' + os.linesep)
                exit(1)
        except Exception as e:
            sys.stderr.write("j2: Command line error ImportUnk: Module " + modpath + ', ' + str(e) + os.linesep)
            if DEBUG_LEVEL>0:
                traceback.print_exc()
            exit(1)

if not args.TEMPLATEPATH:
    args.TEMPLATEPATH = list()

#
# Populate the j2 internal variables
j2['encoding'] = j2_encoding
j2['user'] = getpass.getuser()
j2['host'] = socket.getfqdn()
j2['warning'] = 'WARNING!! DO NOT EDIT THIS FILE, ALL CHANGES WILL BE LOST. THIS FILE IS AUTOGENERATED BY J2.'
j2['version'] = 'J2 Version ' + str(j2['versionnum'])
j2['modules'] = args.MODULE
j2['expressions'] = args.EXPR
j2['date'] = datetime.datetime.now().strftime("%m/%d/%Y")
j2['time'] = datetime.datetime.now().strftime("%I:%M %p")
j2['log1'] = "    processed on " + j2['date'] + " at " + j2['time']
j2['log2'] = "    using modules " + str(j2['modules'])
j2['log3'] = "    with expressions " + str(j2['expressions'])
j2['log4'] = "    by " + str(j2['user']) + "@" + str(j2['host'])


#
# Perform filename template processing
def render_file_name(file):
    DEBUG(1, "Processing FILENAME template " + file)
    try:
        fsload = FileSystemLoader(os.path.dirname(file))
        env = Environment(loader=fsload, trim_blocks=1, newline_sequence=j2_linesep)
        env.globals = globals()
        env.globals.update(locals())
        template = env.get_template(os.path.basename(file))
        result = template.render(env=os.environ)
    except TemplateNotFound:
        sys.stderr.write("j2: Command line error TemplateNotFound: Can't open template " + file + '\n')
        exit(1)
    except TemplateSyntaxError as e:
        # Not sure which is the best here since this is an error in a file as opposed to cmdline error, for now, Ill do both
        sys.stderr.write("j2: Command line error TemplateSyntaxError: " + e.filename + '(' + str(e.lineno) + ') ' + e.message + '\n')
        sys.stderr.write(e.filename + '(' + str(e.lineno) + '): j2 error TemplateSyntaxError:  ' + e.message + '\n')
        exit(1)
    DEBUG(3, "Resulting FILENAME template " + file + " is " + result)
    return(result)


#
# Perform single file template processing
def render_file_template(file, output):
    DEBUG(1, "Processing FILE template " + file)
    templatepath = [os.path.dirname(file)]+args.TEMPLATEPATH
    j2['templatepath'] = os.pathsep.join(templatepath)
    j2['log'] = "J2: Template " + j2['templatepath']
    j2['logall'] = os.linesep.join([j2['log'], j2['log1'], j2['log2'], j2['log3'], j2['log4']])
    try:
        fsload = FileSystemLoader(templatepath, encoding=j2_encoding)
        env = Environment(loader=fsload, trim_blocks=(args.TRIM == 1), newline_sequence = j2_linesep)
        env.globals = globals()
        env.globals.update(locals())
        template = env.get_template(os.path.basename(file))
        #output.write(codecs.encode(template.render(env=os.environ)+os.linesep, j2_encoding))
        output.write(template.render(env=os.environ)+os.linesep)
    except TemplateNotFound as e:
        sys.stderr.write("j2: Command line error TemplateNotFound: Can't open template " + e.name + os.linesep)
        exit(1)
    except TemplateSyntaxError as e:
        # Not sure which is the best here since this is an error in a file as opposed to cmdline error, for now, Ill do both
        sys.stderr.write("j2: Command line error TemplateSyntaxError: " + e.filename + '(' + str(e.lineno) + ') ' + e.message + os.linesep)
        sys.stderr.write(e.filename + '(' + str(e.lineno) + '): j2 error TemplateSyntaxError:  ' + e.message + os.linesep)
        exit(1)


#
# Perform recursive folder template processing
def render_folder_template(folder, dest):
    DEBUG(1, 'Processing FOLDER template "' + folder + '" to location "' + dest + '"')
    if not os.path.exists(dest):
        try:
            os.mkdir(dest)
        except IOError:
            sys.stderr.write("j2: Command line error IOError: Can't create folder " + dest + ' to render output to' + os.linesep)
            exit(1)
    if not os.access(dest, os.W_OK):
        sys.stderr.write("j2: Command line error IOError: Can't open folder " + dest + ' to render output to' + os.linesep)
        exit(1)
    for item in os.listdir(folder):
        if re.search("\.j2n$", item, re.IGNORECASE):
            continue
        if os.path.isdir(folder+os.sep+item):
            DEBUG(2, '  folder item "' + item + '" is folder')
            if item in ignoredirs:    # Skip common SCM folders
                continue
            else:
                if os.path.exists(folder+os.sep+item+'.j2n'):
                    DEBUG(2, '   found j2n for item "' + item + '"')
                    render_folder_template(folder+os.sep+item, dest+os.sep+render_file_name(folder+os.sep + item+".j2n"))
                else:
                    render_folder_template(folder+os.sep+item, dest+os.sep+item)
        else:
            DEBUG(2, '  folder item "' + item + '" is file')
            if os.path.exists(folder+os.sep+item+'.j2n'):
                DEBUG(2, '   found j2n for item "' + item + '"')
                fdest = dest+os.sep+render_file_name(folder+os.sep+item+".j2n")
            else:
                fdest = dest+os.sep+item
            try:
                output = open(fdest, 'wb')
            except IOError:
                sys.stderr.write("j2: Command line error IOError: Can't open file " + fdest + ' to render output to' + os.linesep)
                exit(1)
            render_file_template(folder + os.sep + item, output)
            output.close()


# Execute rendering dependent on FOLDER or FILE
if args.FOLDER:
    if args.OUTPUT == ":NONE:":
        dest = os.getcwd()
    else:
        dest = args.OUTPUT
    for folder in args.template:
        render_folder_template(folder, dest)
else:
    if args.OUTPUT == ":NONE:":
        output = sys.stdout
    else:
        try:
            fdest = args.OUTPUT
            output = open(args.OUTPUT, 'wb')
        except IOError:
            sys.stderr.write("j2: Command line error IOError: Can't open file " + fdest + ' to render output to' + os.linesep)
            exit(1)
    for file in args.template:
        render_file_template(file, output)
    output.close()
