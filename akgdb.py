# GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

from __future__ import print_function

import collections
import codecs
import sys
import os
import multiprocessing
import subprocess
import math
import re
import locale

from collections import defaultdict
from time import strptime, mktime

print("\nLOADING AK-GDB...\n")

TERM = os.environ.get ('TERM')
DEVNULL = open (os.devnull, 'w')

g_help = []
t_help = []
b_help = []
o_help = [("continue", "")]

try:
    TERM_COLUMNS = int (os.popen ('stty size 2>/dev/null', 'r').read ().split () [1])
    RESET_COLOR = '\033[0m'
    ERROR_COLOR = '\033[91m'
    INFO_COLOR = '\033[92m'
    DEBUG_COLOR = '\033[93m'
    GRAPH_COLOR = '\033[94m'
    STRESS_COLOR = '\033[95m'
except:
    TERM_COLUMNS = 80
    RESET_COLOR = ''
    ERROR_COLOR = ''
    INFO_COLOR = ''
    DEBUG_COLOR = ''
    GRAPH_COLOR = ''
    STRESS_COLOR = ''

TERM_SEPLINE = "=" * TERM_COLUMNS


def natural_sort(l, key = str):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda ikey: [ convert(c) for c in re.split('([0-9]+)', key(ikey)) ]
    l.sort (key = alphanum_key)


def safe_strip(str):
    if str is None:
        return None
    else:
        return str.strip()


def safe_int(smthing):
    if smthing is None:
        return smthing
    else:
        return int(str(smthing).strip())


def compose_str_key(*args):
    """Return key object."""

    return "__31x|V__".join(map(unicode, args))


def dictlist_groupby(iter, f):
    """Eager version of itertools.groupby."""

    d = defaultdict(list)
    for item in iter:
        key = f (item)
        d [key].append (item)

    return d

def print_sep(t):
    if t != "":
        t = " " + t + " "

    print (GRAPH_COLOR + TERM_SEPLINE[:4] + t + TERM_SEPLINE[len(t)+4:] + RESET_COLOR, file = sys.stderr)

def print_sep_start(name):
    print()
    print_sep(name)

def print_sep_end():
    print_sep("")
    print()

def print_debug(*parts):
    parts = map (unicode, parts)
    print (GRAPH_COLOR + '::: ' + DEBUG_COLOR + "".join (parts) + RESET_COLOR, file = sys.stderr)

def print_info(*parts):
    parts = map (unicode, parts)
    print (GRAPH_COLOR + '>>> ' + INFO_COLOR + "".join (parts) + RESET_COLOR, file = sys.stderr)


def print_error(*parts):
    parts = map (unicode, parts)
    txt = GRAPH_COLOR + '!!! ' + ERROR_COLOR + "".join (parts) + RESET_COLOR
    print (txt, file = sys.stderr)


## Execution (commands and so on)

def gdb_exec(cmd):
    print_debug(cmd)
    gdb.execute(cmd)

def call(cmd_args, **kw):
    print_debug("sh ", " ".join(cmd_args))
    return subprocess.call (cmd_args, **kw)

# Options: stderr=subprocess.STDOUT  to also capture stderr
def check_output(cmd_args, **kw):
    rc = subprocess.check_output (cmd_args, **kw)
    return rc

class Struct:
    """Convenience class to create object from properties."""

    def __init__(self, **entries):
        self.__dict__.update (entries)

    def __repr__ (self):
        return "Struct" + repr (self.__dict__)


class NeedHelp(BaseException): pass

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
class AkSimpleCmd(gdb.Command):
    def __init__(self, name, f):
        super(AkSimpleCmd, self).__init__(name, gdb.COMMAND_USER)
        self.__f = f

    def invoke(self, args, from_tty):
        self.__f(args)


def ak_cmd(help_grp, desc, **extra):
    def dec(f):
        def ff(*args, **kwds):
            if "no_desc_in_title" in extra:
                title = name
            else:
                title = name + " " + "(" + desc + ")"

            print_sep_start(title)
            try:
                f(*args, **kwds)
            except NeedHelp:
                print_error("Please check arguments:")
                print(f.__doc__)

        name = f.__name__

        if not name.startswith("cmd_"):
            raise error("BaaaaAHhhh, not good name: " + f.__name__)

        name = name[4:]

        help_grp.append((name, desc))
        AkSimpleCmd(name, ff)

        return ff
    return dec

############################################################################################################
############################################################################################################
# Commands

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(g_help, "this help", no_desc_in_title = True)
def cmd_akhelp(args):
    def l_show_grp(l):
        used = 0
        acc = ""
        for name, desc in l:
            if desc == "":
                fmt = STRESS_COLOR + name + RESET_COLOR
                size = len(name)
            else:
                fmt = STRESS_COLOR + name + RESET_COLOR + " - " + desc
                size = len(name) + len(desc) + 3

            delim = ""
            if used == 0:
                used_new = size
            else:
                used_new = used + size + 3
                delim = "   "

            if used_new > TERM_COLUMNS:
                print(acc)
                used = size
                acc = fmt
            else:
                used = used_new
                acc += delim + fmt

        print(acc)

    l_show_grp(g_help)
    print()
    l_show_grp(t_help)
    print()
    l_show_grp(b_help)
    print()
    l_show_grp(o_help)
    print_sep_end()

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(g_help, "make, reset, load")
def cmd_reload(args):
    if call(["make", "debug-only"]) == 0:
        gdb_exec("monitor reset halt")
        gdb_exec("load")
        print()
        print_info("type ", STRESS_COLOR, "continue", INFO_COLOR, " to run\n")

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(g_help, "make, reset, load, cont")
def cmd_restart(args):
    if call(["make", "debug-only"]) == 0:
        gdb_exec("monitor reset halt")
        gdb_exec("load")
        print("")
        print_info("Press CTRL-C to interrupt execution")
        gdb_exec("continue")
        print("")

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(t_help, "", no_desc_in_title = True)
def cmd_threads(args):
    gdb_exec("info threads")

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(t_help, "list variables: [regex]", no_desc_in_title = True)
def cmd_var(args):
    gdb_exec(("info variables " + args).strip())

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(t_help, "list functions: [regex]", no_desc_in_title = True)
def cmd_func(args):
    gdb_exec(("info functions " + args).strip())

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(t_help, "[frames count]", no_desc_in_title = True)
def cmd_stack(args):
    gdb_exec(("info stack " + args).strip())

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(t_help, "frame, args, locals", no_desc_in_title = True)
def cmd_frame(args):
    gdb_exec("info frame")
    gdb_exec("info args")
    gdb_exec("info locals")

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(b_help, "breakpoints")
def cmd_bpl(args):
    gdb_exec("info breakpoints")

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(b_help, "set breakpoint: <LOC>")
def cmd_bp(args):
    """
    LOC may be a line number, function name, or "*" and an address.
    To break on a symbol you must enclose symbol name inside "".
    Example:
       bp "[NSControl stringValue]"
       Or else you can use directly the break command (break [NSControl stringValue])
    """
    if not args: raise NeedHelp()
    gdb_exec("break " + args)

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(b_help, "Clear breakpoint: <LOC>")
def cmd_bpc(args):
    """    LOC may be a line number, function name, or "*" and an address."""
    if not args: raise NeedHelp()
    gdb_exec("clear " + args)

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(b_help, "Enable breakpoint: <N>")
def cmd_bpe(args):
    """    N - Breakpoint number."""
    if not args:
        gdb_exec("info breakpoints")
        print()
        raise NeedHelp()

    gdb_exec("enable " + args)

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(b_help, "Disable breakpoint: <N>")
def cmd_bpd(args):
    """    N - Breakpoint number."""
    if not args:
        gdb_exec("info breakpoints")
        print()
        raise NeedHelp()

    gdb_exec("disable " + args)

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(b_help, "Set temp breakpoint: <LOC>")
def cmd_bpt(args):
    """
    Set a temporary breakpoint.
    This breakpoint will be automatically deleted when hit!.
    LOC may be a line number, function name, or "*" and an address.
    """
    if not args: raise NeedHelp()
    gdb_exec("tbreak " + args)

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(b_help, "Set R/W breakpoint: <EXPR>")
def cmd_bpm(args):
    """    Set a read/write breakpoint on EXPRESSION, e.g. *address."""
    if not args: raise NeedHelp()
    gdb_exec("awatch " + args)

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(b_help, "Set HW breakpoint: <LOC>")
def cmd_bhb(args):
    """
    Set hardware assisted breakpoint.
    LOCATION may be a line number, function name, or "*" and an address.
    """
    if not args: raise NeedHelp()
    gdb_exec("hbreak " + args)

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(b_help, "Set temp HW breakpoint: <LOC>")
def cmd_bht(args):
    """
    Set a temporary hardware breakpoint.
    This breakpoint will be automatically deleted when hit!
    LOCATION may be a line number, function name, or "*" and an address.
    """
    if not args: raise NeedHelp()
    gdb_exec("thbreak " + args)


# ===================================================================================

print_sep("")
print_info("Type ", STRESS_COLOR, "akhelp", RESET_COLOR, " or", INFO_COLOR, " press ", STRESS_COLOR, "F1", RESET_COLOR, " to get our custom help!")
print_info("Type ", STRESS_COLOR, "apropos [subject]", RESET_COLOR, " to find some other command!")
print_info("Press ", STRESS_COLOR, "<enter>", RESET_COLOR, " to repeat last command.")
print_sep_end()
