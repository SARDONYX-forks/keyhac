import os
import sys
import getopt
import shutil
import zipfile
import hashlib
import subprocess
import py_compile

sys.path[0:0] = [
    os.path.abspath( os.path.join( os.path.split(sys.argv[0])[0], '..' ) ),
    ]

import keyhac_resource

#-------------------------------------------

action = "all"

debug = False

option_list, args = getopt.getopt( sys.argv[1:], "d" )
for option in option_list:
    if option[0]=="-d":
        debug = True

if len(args)>0:
    action = args[0]

#-------------------------------------------

PYTHON_DIR = "c:/Python313"

PYTHON = PYTHON_DIR + "/python.exe"

DOXYGEN_DIR = "c:/Program Files/doxygen"

DIST_DIR = "dist/keyhac"
VERSION = keyhac_resource.keyhac_version.replace(".","")
ARCHIVE_NAME = "keyhac_%s.zip" % VERSION

DIST_FILES = {
    "keyhac.exe" :          "keyhac/keyhac.exe",
    "modules" :             "keyhac/modules",
    "python313.dll" :       "keyhac/python313.dll",
    "_config.py" :          "keyhac/_config.py",
    "readme_en.txt" :       "keyhac/readme_en.txt",
    "readme_ja.txt" :       "keyhac/readme_ja.txt",
    "theme/black" :         "keyhac/theme/black",
    "theme/white" :         "keyhac/theme/white",
    "license" :             "keyhac/license",
    "doc/html_en" :         "keyhac/doc/en",
    "doc/html_ja" :         "keyhac/doc/ja",
    "dict/.keepme" :        "keyhac/dict/.keepme",
    "extension/.keepme" :   "keyhac/extension/.keepme",
    }

#-------------------------------------------

def unlink(filename):
    try:
        os.unlink(filename)
    except OSError:
        pass

def makedirs(dirname):
    try:
        os.makedirs(dirname)
    except OSError:
        pass

def rmtree(dirname):
    try:
        shutil.rmtree(dirname)
    except OSError:
        pass

def compilePythonRecursively( src, dst, file_black_list=[], directory_black_list=[] ):

    for root, dirs, files in os.walk( src ):

        for directory_to_remove in directory_black_list:
            if directory_to_remove in dirs:
                dirs.remove(directory_to_remove)

        for file_to_remove in file_black_list:
            if file_to_remove in files:
                files.remove(file_to_remove)

        for filename in files:
            if filename.endswith(".py"):
                src_filename = os.path.join(root,filename)
                dst_filename = os.path.join(dst+root[len(src):],filename+"c")
                print("compile", src_filename, dst_filename )
                py_compile.compile( src_filename, dst_filename, optimize=2 )


def createZip( zip_filename, items ):
    z = zipfile.ZipFile( zip_filename, "w", zipfile.ZIP_DEFLATED, True )
    for item in items:
        if os.path.isdir(item):
            for root, dirs, files in os.walk(item):
                for f in files:
                    f = os.path.normpath(os.path.join(root,f))
                    print( f )
                    z.write(f)
        else:
            print( item )
            z.write(item)
    z.close()


#-------------------------------------------

def target_all():

    target_modules()
    target_document()
    target_dist()
    target_archive()


def target_modules():

    rmtree("modules")

    # compile python source files
    compilePythonRecursively( "c:/python313/Lib", "modules/Lib", 
        directory_black_list = [
            "site-packages",
            "test",
            "tests",
            "idlelib",
            ]
        )
    compilePythonRecursively( "c:/python313/Lib/site-packages/PIL", "modules/Lib/PIL" )
    compilePythonRecursively( "../ckit", "modules/Lib/ckit" )
    compilePythonRecursively( "../pyauto", "modules/Lib/pyauto" )
    compilePythonRecursively( ".", "modules/keyhac", 
        file_black_list = [
            "makefile.py",
            "_config.py",
            "config.py",
            ]
        )

    # copy DLLs
    shutil.copy( "c:/python313/python313.dll", "python313.dll" )

    shutil.copytree( "c:/Python313/DLLs", "modules/DLLs", 
        ignore=shutil.ignore_patterns(
            "tcl*.*",
            "tk*.*",
            "_tk*.*",
            "*.pdb",
            "*_d.pyd",
            "*_d.dll",
            "*_test.pyd",
            "_test*.pyd",
            "*.ico",
            "*.lib"
            )
        )

    makedirs( "modules/Lib/PIL" )
    shutil.copy( "c:/Python313/Lib/site-packages/PIL/_imaging.cp313-win_amd64.pyd", "modules/Lib/PIL/_imaging.pyd" )

    makedirs( "modules/Lib/ckit" )
    shutil.copy( "../ckit/ckitcore.pyd", "modules/Lib/ckit/ckitcore.pyd" )

    makedirs( "modules/Lib/pyauto" )
    shutil.copy( "../pyauto/pyautocore.pyd", "modules/Lib/pyauto/pyautocore.pyd" )

    shutil.copy( "migemo.dll", "modules/DLLs/migemo.dll" )


def target_document():
    rmtree( "doc/html_en" )
    rmtree( "doc/html_ja" )
    makedirs( "doc/obj" )
    makedirs( "doc/html_en" )
    makedirs( "doc/html_ja" )

    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "doc/index_en.txt", "doc/obj/index_en.html" ] )
    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "--template=tool/rst2html_template.txt", "doc/index_en.txt", "doc/obj/index_en.htm_" ] )

    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "doc/index_ja.txt", "doc/obj/index_ja.html" ] )
    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "--template=tool/rst2html_template.txt", "doc/index_ja.txt", "doc/obj/index_ja.htm_" ] )

    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "doc/changes.txt", "doc/obj/changes.html" ] )
    subprocess.call( [ PYTHON, "tool/rst2html_pygments.py", "--stylesheet=tool/rst2html_pygments.css", "--template=tool/rst2html_template.txt", "doc/changes.txt", "doc/obj/changes.htm_" ] )

    subprocess.call( [ DOXYGEN_DIR + "/bin/doxygen.exe", "doc/doxyfile_en" ] )
    shutil.copytree( "doc/image", "doc/html_en/image", ignore=shutil.ignore_patterns("*.pdn",) )

    subprocess.call( [ DOXYGEN_DIR + "/bin/doxygen.exe", "doc/doxyfile_ja" ] )
    shutil.copytree( "doc/image", "doc/html_ja/image", ignore=shutil.ignore_patterns("*.pdn",) )


def target_dist():
    
    rmtree("dist/keyhac")

    src_root = "."
    dst_root = "./dist"
    
    for src, dst in DIST_FILES.items():

        src = os.path.join(src_root,src)
        dst = os.path.join(dst_root,dst)

        print( "copy : %s -> %s" % (src,dst) )
            
        if os.path.isdir(src):
            shutil.copytree( src, dst )
        else:
            makedirs( os.path.dirname(dst) )
            shutil.copy( src, dst )


def target_archive():

    makedirs("dist")

    os.chdir("dist")
    createZip( ARCHIVE_NAME, DIST_FILES.values() )
    os.chdir("..")
    
    fd = open( "dist/%s" % ARCHIVE_NAME, "rb" )
    m = hashlib.md5()
    while 1:
        data = fd.read( 1024 * 1024 )
        if not data: break
        m.update(data)
    fd.close()
    print( "" )
    print( m.hexdigest() )


def target_clean():
    rmtree("dist")
    rmtree("modules")
    rmtree("doc/html_en")
    rmtree("doc/html_ja")


#-------------------------------------------

eval( "target_" + action +"()" )
