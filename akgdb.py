# GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

print("\nLOADING AK-GDB...\n")

class AkHelp(gdb.Command):
    def __init__(self):
        super(AkHelp, self).__init__("akhelp", gdb.COMMAND_USER)

    def invoke(self, args, from_tty):
        print("BLAH")

# Register akhelp command
AkHelp()

print("DONE LOADING AK-GDB!\n")
