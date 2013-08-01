# Define a GDB builder of some kind.

from buildbot.process import factory
from buildbot.process.properties import WithProperties
from buildbot.steps.shell import Compile
from buildbot.steps.shell import Configure
from buildbot.steps.shell import SetProperty
from buildbot.steps.shell import ShellCommand
from buildbot.steps.source import Git
from buildbot.steps.transfer import FileDownload
from gdbcommand import GdbCatSumfileCommand

giturl = 'git://sourceware.org/git/gdb.git'

# Initialize F with some basic build rules.
def _init_gdb_factory(f, conf_flags):
    global giturl
    f.addStep(Git(repourl = giturl, workdir = 'gdb', mode = 'update',
                  reference = '/home/buildbot/Git/gdb/.git'))
    f.addStep(ShellCommand(command=["rm", "-rf", "build"], workdir=".", 
                           description="clean build dir"))
    f.addStep(Configure(command=["../gdb/configure",
                                 '--enable-targets=all'] + conf_flags,
                        workdir="build"))
    f.addStep(Compile(command=["make", "-j4", "all"], workdir="build"))
    f.addStep(Compile(command=["make", "-j4", "info"], workdir="build"))

def _add_summarizer(f):
    f.addStep(GdbCatSumfileCommand(workdir='build/gdb/testsuite',
                                   description='analyze test results'))

def _add_check(f, check_flags, check_env):
    f.addStep(Compile(command=["make", "-k", '-j4', "check"] + check_flags,
                      workdir="build/gdb/testsuite",
                      description='run test suite',
                      env = check_env,
                      # We have to set these due to dejagnu
                      haltOnFailure = False,
                      flunkOnFailure = False))

def _index_build(f):
    f.addStep(SetProperty(command=['pwd'], property='SRCDIR',
                          workdir='gdb/gdb'))
    return [WithProperties (r'CC_FOR_TARGET=/bin/sh %s/cc-with-index.sh gcc',
                            'SRCDIR'),
            WithProperties (r'CXX_FOR_TARGET=/bin/sh %s/cc-with-index.sh g++',
                            'SRCDIR')]

def _gdbserver(f):
    f.addStep(ShellCommand(command = ['mkdir', '-p', 'stuff/boards'],
                           workdir = 'build'))
    f.addStep(ShellCommand(command = ['touch', 'stuff/site.exp'],
                           workdir = 'build'))
    f.addStep(FileDownload(mastersrc = '~/GDB/lib/native-gdbserver.exp',
                           slavedest = 'stuff/boards/native-gdbserver.exp',
                           workdir = 'build'))
    f.addStep(SetProperty(command = ['pwd'], property='STUFFDIR',
                          workdir = 'build/stuff'))
    return { 'DEJAGNU' : WithProperties(r'%s/site.exp', 'STUFFDIR') }

def _make_one_gdb_builder(kind):
    f = factory.BuildFactory()
    _init_gdb_factory(f, [])
    check_flags = []
    check_env = {}
    if kind == 'index':
        check_flags = _index_build(f)
    elif kind == 'dwarf4':
        check_flags = ['RUNTESTFLAGS=--target_board unix/gdb:debug_flags=-gdwarf-4',
                       'FORCE_PARALLEL=yes']
    elif kind == 'm32':
        check_flags = ['RUNTESTFLAGS=--target_board unix/-m32',
                       'FORCE_PARALLEL=yes']
    elif kind == 'gdbserver':
        check_env = _gdbserver(f)
        check_flags = ['RUNTESTFLAGS=--target_board native-gdbserver',
                       'FORCE_PARALLEL=yes']
    _add_check(f, check_flags, check_env)
    _add_summarizer(f)
    return f

# Future build kinds:
# valgrind     Run test suite under valgrind
# bfd64        Build GDB with --enable-64-bit-bfd (32-bit only)
# pie          Build test cases with -fPIE.
# nosysdebug   Configure so that system debuginfo is ignored.

def make_gdb_builder(op_sys, arch, kind = ''):
    """Make a new GDB builder.
OP_SYS is the slave's operating system, e.g., 'f14'.
ARCH is the slave's architecture, e.g., x86_64.
KIND indicates the kind of builder to make.  It is a string.
The default, indicated by the empty string, is to make a basic builder.
Other valid values are:
  dwarf4       Run test suite with -gdwarf-4.
  gdbserver    Run test suite against gdbserver.
  index        Run test suite with .gdb_index files.
  m32          Build GDB and run all tests with -m32 (64-bit only).
"""
    name = 'gdb-' + op_sys + '-' + arch
    if kind != '':
        name = name + '-' + kind
    return { 'name' : name,
             'slavenames' : [ name ],
             'builddir' : name,
             'factory' : _make_one_gdb_builder(kind)
             }
