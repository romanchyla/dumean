import os
import sys



try:
    # tries importing PyLucene if installed
    # due to the way we build pyjama (as --shared --import lucene) we usually
    # depend on the presence of lucene package, and that one must be imported
    # first
    import lucene
except:
    lucene = None
    sys.stderr.write('PyLucene is not installed - certain components will not work. '
                'If you do not want this dependency, you may want to recompile in a standalone mode. See build.xml '
                'for instructions.\n')

try:
    # tries import dumeanj if installed
    import dumeanj
except:
    dumeanj = None
    sys.stderr.write('Cannot import dumeanj module - we will continue, but certain components will not work. I warned you!\n')

try:
    import jcc
    if dumeanj:
        _jcc_module = dumeanj
    elif lucene:
        _jcc_module = lucene
    else:
        _jcc_module = jcc
except:
    raise Exception('You miss python JCC module, none of the java services can work without it')



def get_java_module():
    """Finds, imports and returns the python module which contains the JAVA programs
    and also the compiled JCC wrapper - using this module, we communicate with JAVA
    programs"""
    if not dumeanj:
        raise ImportError('dumeanj module is not available - install it first, before using this component.')
    return dumeanj


def start_jvm(clspath='', vmargs=''):
    """Starts the JVM - note that only the first initVM() is effective for java VM!
    Make sure you pass important arguments for the first call, because they will
    set the environment of the Java VM
    @keyword clspath: platform-separator separated values that will be passed to
        the Java VM
    @keyword vmargs: other arguments, comma-separated to pass to the java VM
    @return: JVM object (either new one or already existing one)"""


    #initialize the JVM if not already initialized
    jvm = _jcc_module.getVMEnv()
    if not jvm:
        classpath = []
        if clspath:
            classpath.append(clspath)
        if dumeanj:
            classpath.append(dumeanj.CLASSPATH)
        if lucene:
            classpath.append(lucene.CLASSPATH)
        jvm = _jcc_module.initVM(os.pathsep.join(classpath), vmargs=vmargs)

        if lucene != _jcc_module:
            lucene.initVM(lucene.CLASSPATH)
    elif vmargs:
        raise Exception('initVM() was already started, the second call will be ineffective. Please make sure you are initializing components in the right order!')

    return jvm

def attach():
    """Attaches the current thread to the JavaVM, is called by some of pyjamic
    modules"""
    jvm = _jcc_module.getVMEnv()
    jvm.attachCurrentThread()


