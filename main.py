import ast
import os
import sys
import curses     as cur
import datetime   as dttm
import logging    as lg
import subprocess as sp
import traceback  as tb
import typing     as ty

sys.path.insert(1, os.path.dirname(__file__) + os.sep + "core")
import engine
sys.path.pop(1)

FATAL             = 60
prevKeyboardDelay = None
try:
    modeCommRunLower  = sp.run(("MODE", ), capture_output=True, shell=True,
                               text=True, check=True).stdout.lower()
    txt               = [i for i in modeCommRunLower.splitlines()
                         if "delay" in i]
    prevKeyboardDelay = int(txt[0].split(":")[1].strip())
    sp.run("mode CON: DELAY=0", check=True, shell=True)

except sp.CalledProcessError:
    print("Cannot set keyboard delay to 0")


class CustomLogger(lg.getLoggerClass()):
    """
    Custom logger extending the logging.Logger class to add separate 
    functionality to the FATAL log level.
    """
    def __init__(self, name: str, level: int | str = lg.NOTSET) -> None:
        super().__init__(name, level)
        lg.addLevelName(FATAL, "FATAL")
    
    def fatal(self, msg: str, *args: ty.Any, **kwargs: ty.Any) -> None:
        if self.isEnabledFor(FATAL):
            self._log(FATAL, msg, args, **kwargs, stacklevel=2)


class CustomLogFormatter(lg.Formatter):
    """
    To apply custom formatting to the log message (like whitespace stripping).
    """
    def __init__(self, fmt: str | None = None, datefmt: str | None = None,
                 style: ty.Literal['%'] | ty.Literal['{'] | ty.Literal['$'] = "%",
                 validate: bool = True, *,
                 defaults: ty.Mapping[str, ty.Any] | None = None) -> None:
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)
    
    def format(self, record: lg.LogRecord) -> str:
        record.msg  = record.getMessage().strip()
        record.msg2 = record.msg.splitlines()[-1].strip().split(' ')[0][:-1]
        return super().format(record)


def parseArgs() -> tuple[int, dict[str, ty.Any] | str]:
    """
    Parse command line arguments.
    > return: If arguments are valid, argument data in the form of a 
              dictionary, where keys are the argument names and values are 
              the argument values. Else, an integer representing the error.
              Error codes:
              1: Invalid argument
              2: Invalid argument value
              3: Value expected for argument
    """
    argData: dict[str, ty.Any]
    i       = 1
    argData = {}
    argLen  = len(sys.argv)

    if "-h" in sys.argv or "--help" in sys.argv:
        return -1, ''
    
    while i < argLen:
        curArg = sys.argv[i].lower()
        try:
            if curArg in ("-f", "--fps"):
                argData["fps"]  = float(sys.argv[i + 1])
                i              += 1
            elif curArg in ("-d", "--debug"):
                if "debug" in argData:
                    argData["debug"].append(sys.argv[i + 1])
                else:
                    argData["debug"] = [sys.argv[i + 1]]
                if set([i.lower() for i in argData["debug"]]) > {"fps", "objc"}:
                    return 2, sys.argv[i]
                i += 1
            elif curArg in ("-pv", "--player-vel"):
                if not len(playerVel := ast.literal_eval(sys.argv[i + 1])):
                    return 1, sys.argv[i]
                argData["playerVel"] =  playerVel
                i                    += 1
            elif curArg == "--wall-cor":
                argData["wallCOR"]  = float(sys.argv[i + 1])
                i                  += 1
            else:
                # Invalid (i.e. unknown) argument
                return 1, sys.argv[i]
        except ValueError:
            # Invalid argument value
            return 2, sys.argv[i]
        except IndexError:
            # Expected one value after argument
            return 3, sys.argv[i]
        i += 1
    
    return 0, argData


def initLogger() -> lg.Logger:
    """
    Initialise logging components and logger.
    > return: Logger object after applying all formatting rules and handlers
    NOTE: Please note that the Logger class is changed in this function with 
          the function logging.setLogger
    """
    lg.captureWarnings(True)
    lg.setLoggerClass(CustomLogger)
    lgr         = lg.getLogger(__name__)
    # TODO: Don't think console handler is required. Simplify the output, or 
    # remove it later!
    conHdler    = lg.StreamHandler()
    fileHdler   = lg.FileHandler(os.path.dirname(__file__) + os.sep + "log.log",
                                'a', encoding="utf-8")
    
    cnFormatter = CustomLogFormatter(
        fmt=("%(levelname)s:%(module)s:"
            "%(funcName)s:%(msg2)s"),
        datefmt="%z/%d-%m-%Y/%H:%M:%S"
    )
    lgFormatter = CustomLogFormatter(
        fmt=("[%(asctime)s.%(msecs)03d]\n%(levelname)s:%(module)s:"
            "%(funcName)s:\n%(message)s\n--------"),
        datefmt="%z/%d-%m-%Y/%H:%M:%S"
    )
    
    conHdler.setFormatter(cnFormatter)
    fileHdler.setFormatter(lgFormatter)
    lgr.setLevel(lg.WARNING)
    lgr.addHandler(conHdler)
    lgr.addHandler(fileHdler)
    
    return lgr


def main(stdscr: cur.window, args: dict[str, ty.Any], lgr: lg.Logger) -> None:
    """
    Wrapped function for the curses program.
    > param stdscr: curses.window object for the representing the screen
    > param args: Arguments passed to this program after processing
    > param lgr: CustomLogger object, for logging
    """
    stdscr.leaveok(True)
    cur.raw()
    cur.noecho()
    stdscr.keypad(True)
    stdscr.nodelay(True)
    cur.curs_set(0)

    eng = engine.Engine(stdscr, lgr, args)
    eng.start()


if __name__ == "__main__":
    try:
        args = parseArgs()
        if args[0] == -1:
            print((
                "Arguments\n"
                "\t-f, --fps\n"
                "\t\tSpecify the target frame rate\n"
                "\t-d, --debug <val>\n"
                "\t\tEnable debug options. Valid values: fps\n"
                "\t-pv, --player-vel <val>\n"
                "\t\tAdjust initial velocity of the player object. Value must "
                "be in Python list syntax\n"
                "\t--wall-cor <val>\n"
                "\t\tAdjust wall, ground and ceiling COR. Value must be a "
                "floating-point number"
            ).expandtabs(4))
        if args[0] == 1:
            print(f"Invalid argument: {args[1]}")
        elif args[0] == 2:
            print(f"Invalid argument value for {args[1]}")
        elif args[0] == 3:
            print(f"One argument value expected for {args[1]}")
        if args[0]:
            sys.exit(args[0] if args[0] != -1 else 0)
        lgr = initLogger()
        cur.wrapper(main, args[1], lgr)

    except Exception as e:
        # Manualo logging. Yeah, I know, it's crap.
        print(f"FATAL:UnknownErr:({e.__class__.__name__}) {e}")
        with open("fatalLog.log", 'a') as f:
            f.write(f"{dttm.datetime.now().strftime(r"[%d-%m-%Y/%H:%M:%S.%f]")}\n"
                    f"{tb.format_exc().strip()}\n--------\n")

    except KeyboardInterrupt:
        pass

    finally:
        try:
            sp.run(("MODE", "CON:", f"DELAY={prevKeyboardDelay}"), check=True,
                   shell=True)
        except sp.CalledProcessError:
            print("Unable to set keyboard delay to original value; you can "
                  "try to set it yourself.\nOriginal value: "
                  f"{prevKeyboardDelay}")
