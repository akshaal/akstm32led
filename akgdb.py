# GNU GPL blah blah blah (C) Akshaal (Evgeny Chukreev), 2017 blah blah blah
# Some code is borrowed from python-gdb-dashboard, credits, stuff and karma goes this way
# +++ other gdbinits maybe
# Some code is based upon code by Carl Allendorph

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
import pygments
import pygments.lexers
import pygments.formatters

from collections import defaultdict
from time import strptime, mktime

print("\nLOADING AK-GDB...\n")

PYGMENTS_STYLE="paraiso-dark"
SRC_CTX = 4 # Number of lines to show by src command
HIST_LIMIT = 20

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
    UNIMP_COLOR = '\033[90m'
except:
    TERM_COLUMNS = 80
    RESET_COLOR = ''
    ERROR_COLOR = ''
    UNIMP_COLOR = ''
    INFO_COLOR = ''
    DEBUG_COLOR = ''
    GRAPH_COLOR = ''
    STRESS_COLOR = ''

TERM_SEPLINE = "=" * TERM_COLUMNS


F_CACHE = {}
REG_TABLE = {}

uint32_t = gdb.lookup_type("uint32_t")
uint16_t = gdb.lookup_type("uint16_t")

def format_address(address):
    pointer_size = gdb.parse_and_eval('$pc').type.sizeof
    return ('0x{{:0{}x}}').format(pointer_size * 2).format(address)

def to_unsigned(value, size=8):
    # values from GDB can be used transparently but are not suitable for
    # being printed as unsigned integers, so a conversion is needed
    return int(value.cast(gdb.Value(0).type)) % (2 ** (size * 8))

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

def gdb_capture(cmd):
    return gdb.execute(cmd, to_string = True)

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

class FreeRtosListInspector:
    ListType = gdb.lookup_type("List_t")

    def __init__(self, handle):
        self._list = None
        self.assign(handle)

    def assign(self, listObj):
        try:
            if listObj.type == FreeRtosListInspector.ListType:
                self._list = listObj
                return
            else:
                raise TypeError("Invalid List Object Type!")
        except Exception as exc:
            pass

        symbol, methodObj = gdb.lookup_symbol(listObj)
        if symbol != None:
            self._list = symbol.value()
        else:
            addrInt = int(listObj, 0)
            listObjPtr = gdb.Value(addrInt).cast(ListInspector.ListType.pointer())
            self._list = listObjPtr.dereference()

    def get_elements(self, castTypeStr = None, startElem = 1):
        if self._list == None:
            raise ValueError("Invalid List Object - Possibly Failed to Initialize!")

        castType = None
        if castTypeStr != None:
            if type(castTypeStr) == str:
                try:
                    castType = gdb.lookup_type(castTypeStr).pointer()
                except:
                    print("Failed to find type: %s" % CastTypeStr)
            elif type(castTypeStr) == gdb.Type:
                castType = castTypeStr.pointer()

        resp = []
        numElems = self._list['uxNumberOfItems']
        index = self._list['pxIndex']

        if numElems > 0 and numElems < 200:
            if startElem == 0:
                curr = index
            else:
                curr = index['pxPrevious']

            for i in range(0, numElems):
                owner = curr['pvOwner']

                ownerObj = None
                if castType == None:
                    ownerObj = owner.cast(uint32_t)
                else:
                    ownerObj = owner.cast(castType).dereference()

                itemVal = curr['xItemValue']
                resp.append( (ownerObj, itemVal.cast(uint32_t) ))
                curr = curr['pxPrevious']

        return(resp)

class NeedHelp(BaseException): pass

class Highlighter():
    def __init__(self, filename):
        self.formatter = pygments.formatters.Terminal256Formatter(style = PYGMENTS_STYLE)
        self.lexer = pygments.lexers.get_lexer_for_filename(filename)

    def process(self, source):
        return pygments.highlight(source, self.lexer, self.formatter).rstrip('\n')

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

            if  "no_title" not in extra:
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
    print()
    print_info(INFO_COLOR, "Press ", STRESS_COLOR, "F1", RESET_COLOR, " to get our custom help!")
    print_info(INFO_COLOR, "Press ", STRESS_COLOR, "F2", RESET_COLOR, " for dashboard.")

    print_sep_end()

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(g_help, "make, reset, load")
def cmd_reload(args):
    if call(["make", "debug-only"]) == 0:
        F_CACHE = {}
        gdb_exec("monitor reset halt")
        gdb_exec("load")
        print()
        print_info("type ", STRESS_COLOR, "continue", INFO_COLOR, " to run\n")

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(g_help, "make, reset, load, cont")
def cmd_restart(args):
    if call(["make", "debug-only"]) == 0:
        F_CACHE = {}
        gdb_exec("monitor reset halt")
        gdb_exec("load")
        print("")
        print_info("Press CTRL-C to interrupt execution")
        gdb_exec("continue")
        print("")

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
def get_tasks():
    def print_task(dct, t):
        numb, task, state = t
        topStack = task['pxTopOfStack']
        stackBase = task['pxStack']
        highWater = topStack - stackBase
        taskName = task['pcTaskName'].string()
        taskPriority = task['uxPriority']

        pid = int(task.address.cast(uint32_t))

        style = DEBUG_COLOR if state == "ready" else (ERROR_COLOR if state == "blocked" else INFO_COLOR)

        dct[pid] = RESET_COLOR + "Name: " + style + str(taskName) + RESET_COLOR + "  prio: " + style + str(taskPriority) + RESET_COLOR + "  stack: " + style + str(highWater) + RESET_COLOR

    def print_tasks(dct, tasks):
        for t in tasks:
            print_task(dct, t)

    def add_tasks(acc, tasks, state):
        for task, _ in tasks:
            numb = task['uxTCBNumber']
            acc.append((numb, task, state))

    blocked = FreeRtosListInspector("xSuspendedTaskList").get_elements("TCB_t")
    delayed1 = FreeRtosListInspector("xDelayedTaskList1").get_elements("TCB_t")
    delayed2 = FreeRtosListInspector("xDelayedTaskList2").get_elements("TCB_t")
    ready = []

    pxReadyTasksListsSym, _ = gdb.lookup_symbol("pxReadyTasksLists")
    readyLists = pxReadyTasksListsSym.value()

    minIndex, maxIndex = readyLists.type.range()
    for i in range(int(minIndex), int(maxIndex) + 1):
        ready.extend(FreeRtosListInspector(readyLists[i]).get_elements("TCB_t", 0 if i == 0 else 1))

    allt = []

    add_tasks(allt, ready, "ready")
    add_tasks(allt, blocked, "blocked")
    add_tasks(allt, delayed1, "delayed1")
    add_tasks(allt, delayed2, "delayed2")

    dct = {}
    print_tasks(dct, allt)
    return dct

@ak_cmd(t_help, "", no_desc_in_title = True)
def cmd_threads(args):
    tasks = get_tasks()

    selected_thread = gdb.selected_thread()
    selected_frame = gdb.selected_frame()

    for thread in gdb.Inferior.threads(gdb.selected_inferior()):
        is_selected = (thread.ptid == selected_thread.ptid)

        style = DEBUG_COLOR if is_selected else INFO_COLOR

        number = style + str(thread.num) + RESET_COLOR
        ptid = thread.ptid[1] or thread.ptid[2]
        tid = style + str(ptid) + RESET_COLOR

        info = '[{}] id {}'.format(number, tid)

        task = tasks.get(int(ptid), None)

        if task:
            info += " " + task

        if thread.name:
            info += ' name {}'.format(style + thread.name + RESET_COLOR)

        # switch thread to fetch frame info
        thread.switch()
        frame = gdb.newest_frame()
        info += ' ' + stack_get_pc_line(frame, style)

        print(info)

    # restore thread and frame
    selected_thread.switch()
    selected_frame.select()

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(t_help, "list variables: [regex]", no_desc_in_title = True)
def cmd_var(args):
    gdb_exec(("info variables " + args).strip())

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(t_help, "list functions: [regex]", no_desc_in_title = True)
def cmd_func(args):
    gdb_exec(("info functions " + args).strip())

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
def stack_get_pc_line(frame, style):
    frame_pc = format_address(frame.pc())
    info = 'from {}'.format(frame_pc)
    if frame.name():
        frame_name = style + frame.name() + RESET_COLOR
        try:
            # try to compute the offset relative to the current function
            value = gdb.parse_and_eval(frame.name()).address

            # it can be None even if it is part of the "stack" (C++)
            if value:
                func_start = to_unsigned(value)
                offset = frame.pc() - func_start
                frame_name += '+' + style + str(offset) + RESET_COLOR
        except gdb.error:
            pass  # e.g., @plt

        info += ' in {}'.format(frame_name)
        sal = frame.find_sal()
        if sal.symtab:
            file_name = style + sal.symtab.filename + RESET_COLOR
            file_line = style + str(sal.line) + RESET_COLOR
            info += ' at {}:{}'.format(file_name, file_line)
    return info

@ak_cmd(t_help, "[frames count]", no_desc_in_title = True)
def cmd_stack(args):
    limit = 3
    if args: limit = int(args.strip())

    def fetch_frame_info(frame, data, prefix):
        lines = []
        for elem in data or []:
            name = elem.sym
            value = str(elem.sym.value(frame))
            lines.append('{} {} = {}'.format(prefix, STRESS_COLOR + str(name) + RESET_COLOR, value))
        return lines

    selected_index = 0
    frame = gdb.newest_frame()

    while frame:
        if frame == gdb.selected_frame():
            break

        frame = frame.older()
        selected_index += 1

    # format up to "limit" frames
    frames = []
    number = selected_index
    more = False

    while frame:
        sal = frame.find_sal()
        if sal and sal.symtab:
            fname = sal.symtab.fullname()
            lines = get_cached_src_lines(fname)
            line_num = sal.line
            src_line = DEBUG_COLOR + "SRC: " + RESET_COLOR + lines[line_num-1] + RESET_COLOR
        else:
            src_line = UNIMP_COLOR  + "[no source]" + RESET_COLOR

        # the first is the selected one
        selected = len(frames) == 0

        # fetch frame info
        style = DEBUG_COLOR if selected else INFO_COLOR

        frame_id = style + str(number) + RESET_COLOR

        info = stack_get_pc_line(frame, style)

        frame_lines = []
        frame_lines.append('[{}] {}'.format(frame_id, info))

        # fetch frame arguments and locals
        decorator = gdb.FrameDecorator.FrameDecorator(frame)
        frame_args = decorator.frame_args()
        args_lines = fetch_frame_info(frame, frame_args, 'arg')
        if args_lines:
            frame_lines.extend(args_lines)
        else:
            frame_lines.append(UNIMP_COLOR + '(no arguments)' + RESET_COLOR)

        frame_locals = decorator.frame_locals()
        locals_lines = fetch_frame_info(frame, frame_locals, 'loc')
        if locals_lines:
            frame_lines.extend(locals_lines)
        else:
            frame_lines.append(UNIMP_COLOR + '(no locals)' + RESET_COLOR)

        frame_lines.append(src_line)

        # add frame
        frames.append(frame_lines)

        # next
        frame = frame.older()
        number += 1

        # check finished according to the limit
        if limit and len(frames) == limit:
            # more frames to show but limited
            if frame:
                more = True
            break

    # format the output
    lines = []
    for frame_lines in frames:
        lines.extend(frame_lines)
        lines.append("")

    # add the placeholder
    if more:
        lines.append('[{}]'.format(INFO_COLOR + '+' + RESET_COLOR))

    for line in lines:
        print(line)

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

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
def get_cached_src_lines(fname):
    if fname in F_CACHE:
        return F_CACHE[fname]
    else:
        highlighter = Highlighter(fname)
        with open(fname) as source_file:
            lines = highlighter.process(source_file.read()).split('\n')
            F_CACHE[fname] = lines

        return lines

@ak_cmd(o_help, "Source code: [lines]")
def cmd_src(args):
    sal = gdb.selected_frame().find_sal()
    line_num = sal.line
    if not line_num:
        print_info("No line (", sal, ")")
        return

    print_info("Line: ", STRESS_COLOR, line_num, INFO_COLOR, "  File: ", sal.symtab.filename)

    fname = sal.symtab.fullname()
    lines = get_cached_src_lines(fname)

    ctx = SRC_CTX
    if args: ctx = int(args.strip())

    start = max(line_num - ctx - 1, 0)
    end = min(line_num + ctx, len(lines))

    number_format = '{{:>{}}}'.format(len(str(end)))
    for number, line in enumerate(lines[start:end], start + 1):
        line = number_format.format(number) + "  " + RESET_COLOR + line
        if number == line_num:
            line = DEBUG_COLOR + line
        else:
            line = UNIMP_COLOR + line

        print(line)

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(o_help, "Assembler: [lines]")
def cmd_asm(args):
    ctx = SRC_CTX
    if args: ctx = int(args)

    frame = gdb.selected_frame()
    disassemble = frame.architecture().disassemble
    try:
        # Get function boundaries
        output = gdb_capture('disassemble').split('\n')
        start = int(re.split('[ :]', output[1][3:], 1)[0], 16)
        end = int(re.split('[ :]', output[-3][3:], 1)[0], 16)
        asm = disassemble(start, end_pc = end)

        pc_index = next(index for index, instr in enumerate(asm) if instr['addr'] == frame.pc())
        start = max(pc_index - ctx, 0)
        end = pc_index + ctx + 1
        asm = asm[start:end]

        line_info = gdb.find_pc_line(frame.pc())
        line_info = line_info if line_info.last else None
    except (gdb.error, StopIteration):
        # stripped file or some other crap
        asm = disassemble(frame.pc(), count=2 * ctx + 1)

    # Function stuff
    func_start = None
    if frame.name():
        try:
            value = gdb.parse_and_eval(frame.name()).address
            func_start = to_unsigned(value)
        except gdb.error:
            pass # whatever

    highlighter = Highlighter("dump.s")

    max_length = max(instr['length'] for instr in asm)
    inferior = gdb.selected_inferior()

    for index, instr in enumerate(asm):
        addr = instr['addr']
        length = instr['length']
        text = instr['asm']
        addr_str = format_address(addr)

        # fetch and format opcode
        region = inferior.read_memory(addr, length)
        opcodes = (' '.join('{:02x}'.format(ord(byte)) for byte in region))
        opcodes += (max_length - len(region)) * 3 * ' ' + ' '

        # compute the offset if available
        if func_start:
            max_offset = len(str(asm[-1]['addr'] - func_start))
            offset = str(addr - func_start).ljust(max_offset)
            func_info = '{}+{} '.format(frame.name(), offset)
        else:
            func_info = '? '

        text = highlighter.process(text.replace("#", "$$$$").replace(";", "#")).replace("#", ";").replace("$$$$", "#")

        if addr == frame.pc():
            c = DEBUG_COLOR
        elif line_info and line_info.pc <= addr < line_info.last:
            c = INFO_COLOR
        else:
            c = UNIMP_COLOR

        print(c + addr_str, opcodes.upper(), func_info[-14:], RESET_COLOR + text + RESET_COLOR)

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(o_help, "registers")
def cmd_regs(args):
    def format_value(value):
        try:
            if value.type.code in [gdb.TYPE_CODE_INT, gdb.TYPE_CODE_PTR]:
                int_value = to_unsigned(value, value.type.sizeof)
                value_format = '0x{{:0{}x}}'.format(2 * value.type.sizeof)
                return value_format.format(int_value)
        except (gdb.error, ValueError):
            pass # convert to unsigned but preserve code and flags information

        return str(value)

    # fetch registers status
    registers = []

    for reg_info in gdb_capture('info registers').strip().split('\n'):
        # fetch register and update the table
        name = reg_info.split(None, 1)[0]

        # Exclude registers with a dot '.' or parse_and_eval() will fail
        if '.' in name: continue

        value = gdb.parse_and_eval('${}'.format(name))
        string_value = format_value(value)

        changed = REG_TABLE.get(name, '') != string_value
        REG_TABLE[name] = string_value

        registers.append((name, string_value, changed))

    # split registers in rows and columns, each column is composed of name,
    # space, value and another trailing space which is skipped in the last
    # column (hence term_width + 1)
    max_name = max(len(name) for name, _, _ in registers)
    max_value = max(len(value) for _, value, _ in registers)
    max_width = max_name + max_value + 2
    per_line = int((TERM_COLUMNS + 1) / max_width) or 1

    # redistribute extra space among columns
    extra = int((TERM_COLUMNS + 1 - max_width * per_line) / per_line)

    if per_line == 1:
        # center when there is only one column
        max_name += int(extra / 2)
        max_value += int(extra / 2)
    else:
        max_value += extra

    # format registers info
    partial = []
    for name, value, changed in registers:
        styled_name = UNIMP_COLOR + name.rjust(max_name) + RESET_COLOR
        value_style = DEBUG_COLOR if changed else RESET_COLOR
        styled_value = value_style + value.ljust(max_value) + RESET_COLOR

        partial.append(styled_name + ' ' + styled_value)

    for i in range(0, len(partial), per_line):
        print(' '.join(partial[i:i + per_line]).rstrip())

# - - - - - ---------------------------- --- - - - - - - - - - -  - - - - - -- - - - - - - - - - - - - - -
@ak_cmd(o_help, "dashboard", no_title = True)
def cmd_d(args):
    cmd_stack("")
    cmd_threads("")
    cmd_asm("")
    cmd_regs("")
    cmd_src("")

# ===================================================================================

print_sep("")
print_info("Type ", STRESS_COLOR, "akhelp", RESET_COLOR, " or", INFO_COLOR, " press ", STRESS_COLOR, "F1", RESET_COLOR, " to get our custom help!")
print_info("Type ", STRESS_COLOR, "apropos [subject]", RESET_COLOR, " to find some other command!")
print_info("Press ", STRESS_COLOR, "<enter>", RESET_COLOR, " to repeat last command.")
print_sep_end()
