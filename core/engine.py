import random
import time
import curses    as cur
import logging   as lg
import objects   as objs
import traceback as tb
import typing    as ty

global sd


class Engine:
    def __init__(self, stdscr: cur.window, lgr: lg.Logger,
                 args: dict[str, ty.Any]) -> None:
        # TODO: Remove these test variables!
        self.testFile     = open("test.txt", 'w+')
        self.testFileBin  = open("testBin.bin", 'wb+')
        self.roughTimeCnt = 0
        self.movObjs  : list[objs.MovableObj]
        self.immovObjs: list[objs.ImmovableObj]
        self.stdscr       = stdscr
        self.lgr          = lgr
        self.err          = 0
        self.lastTime     = time.perf_counter()
        self.movObjs      = []
        self.immovObjs    = []
        self.movObjsApp   = self.movObjs.append
        self.immovObjsApp = self.immovObjs.append
        self.termSize     = self.stdscr.getmaxyx()
        self.lWall        = objs.BoundaryObj("lWall", (0, 0),
                                             self.termSize[0], 1, invis=True)
        self.rWall        = objs.BoundaryObj("rWall", (self.termSize[1] - 1, 0),
                                             self.termSize[0], 1, invis=True)
        self.ceiling      = objs.BoundaryObj("ceiling", (0, 0),
                                             self.termSize[1], 1, invis=True)
        self.ground       = objs.BoundaryObj("ground", (0, self.termSize[0] - 1),
                                             self.termSize[1], 1, invis=True)
        self.tgtFrameRt   = 1e1000
        self.debugFPS     = False
        self.debugObjCnt  = False
        
        # Update with argument data
        if "fps" in args:
            self.tgtFrameRt = args["fps"]
        if "debug" in args:
            lowerDebug = [i.lower() for i in args["debug"]]
            if "fps" in lowerDebug:
                self.debugFPS = True
            if "objc" in lowerDebug:
                self.debugObjCnt = True
        if "playerVel" in args:
            self.player.vel = args["playerVel"]
        if "wallCOR" in args:
            self.lWall.cor   = args["wallCOR"]
            self.rWall.cor   = args["wallCOR"]
            self.ceiling.cor = args["wallCOR"]
            self.ground.cor  = args["wallCOR"]

    def _createTestObjs(self, n: int = 16) -> int | None:
        """
        This is a temporary function.
        TODO: Therefore, remove this!
        """
        syms = ('+', '-', '*', '/', '\\', '%', '$', '^', '!', '&', ':', ';',
                '?', '>', '<', '=')
        if n > len(syms):
            return 1
        for i in range(n):
            self._createMovObj(
                objs.Sq,
                f"test{i}",
                [random.randint(1, self.termSize[1] - 1), random.randint(1, self.termSize[1] - 1)],
                [random.randint(10, 30), random.randint(7, 20)],
                # [random.randint(6, 15), random.randint(4, 10)],
                [0, 10], 1, 2, char=syms[i]
            )
        return None
    
    def _createMovObj(self, obj: type[objs.MovableObj], *args: ty.Any,
                      **kwargs: ty.Any) -> objs.MovableObj:
        self.movObjsApp(temp := obj(*args, **kwargs))
        return temp
    
    def _createImmovObj(self, obj: type[objs.ImmovableObj], *args: ty.Any,
                        **kwargs: ty.Any) -> objs.ImmovableObj:
        self.immovObjsApp(temp := obj(*args, **kwargs))
        return temp

    def _doesObjCrossBndries(self, obj: objs.ImmovableObj | objs.MovableObj) \
            -> tuple[bool, bool, bool, bool]:
        """
        Checks whether a given Movable or Immovable object cross the boundaries.
        TODO: Make this goddamn comment more descriptive.
        > param obj: Object to check (?)
        > return: A tuple of length four, containing the data as per their 
                  position:
                  1: Left wall boundary
                  2: Right wall boundary
                  3: Ceiling boundary
                  4: Ground boundary
        """
        lWallCross   = obj.pos[0] - 1 < self.lWall.pos[0]
        rWallCross   = obj.pos[0] + obj.cols > self.rWall.pos[0]
        ceilingCross = obj.pos[1] - 1 < self.ceiling.pos[1]
        groundCross  = obj.pos[1] + obj.lns > self.ground.pos[1]
        return lWallCross, rWallCross, ceilingCross, groundCross
    
    def _consScr(self, fps: float) -> None:
        """
        Construct each frame to be rendered.
        Draws borders, and add a frame counter at the top-right corner.
        NOTE: The player object needs to have the name "player" so as to be 
              rendered on top.
        > param fps: Floating-point value representing number of frames 
                     rendered in the last second
        """
        # TODO: Might need to implement such that the player is always 
        # rendered on top, i.e. player should always be visible. Keep that in 
        # mind, if needed.
        self.stdscr.clear()
        for obj in self.movObjs:
            if obj.name == "player":
                continue
            for i, line in enumerate(obj.txt.splitlines()):
                self.stdscr.addnstr(int(obj.pos[1]) + i, int(obj.pos[0]),
                                    line, self.termSize[1])
        for i, line in enumerate(self.player.txt.splitlines()):
            self.stdscr.addnstr(int(self.player.pos[1]) + i,
                                int(self.player.pos[0]),
                                line, self.termSize[1])
        self.stdscr.border()
        self.stdscr.addnstr(0, self.termSize[1] - len(f"{fps:<07.7f}") - 5,
                            f"FPS={fps:<07.7f}", self.termSize[1],
                            cur.A_REVERSE) if self.debugFPS else None
        self.stdscr.addnstr(self.termSize[0] - 1, self.termSize[1] \
                                - (len(str(tmp := (len(self.movObjs) + 5)))) \
                                - len(str(self.roughTimeCnt)) - 12,
                           f"@T={self.roughTimeCnt} OBJCNT={tmp}",
                           self.termSize[1], cur.A_REVERSE) \
                               if self.debugObjCnt else None
    
    def update(self, dt: float) -> None:
        """
        Update all objects.
        > param dt: Floating-point number representing seconds passed after 
                    last update (delta time)
        """
        for obj in self.movObjs:
            bndryData = self._doesObjCrossBndries(obj)

            obj.vel[0] += obj.accl[0] * dt
            obj.vel[1] += obj.accl[1] * dt
            obj.pos[0] += obj.vel[0] * dt
            obj.pos[1] += obj.vel[1] * dt

            # If the object crosses the boundaries, move the object inside 
            # the boundaries
            obj.pos[0] = max(0, min(obj.pos[0], self.termSize[1] - obj.cols))
            obj.pos[1] = max(0, min(obj.pos[1], self.termSize[0] - obj.lns))

            if bndryData[0] and (obj.vel[0] < 0 or obj.pos[0] <= 1):
                obj.vel[0] = -obj.vel[0] * self.lWall.cor
                obj.pos[0] = 1
            if bndryData[1] and (obj.vel[0] > 0
                                 or obj.pos[0] + obj.cols >= self.termSize[1]):
                obj.vel[0] = -obj.vel[0] * self.rWall.cor
                obj.pos[0] = self.termSize[1] - obj.cols + 1 - 2
            if bndryData[2] and (obj.vel[1] > 0 or obj.pos[1] <= 1):
                obj.vel[1] = -obj.vel[1] * self.ceiling.cor
                obj.pos[1] = 1
            if bndryData[3] and (obj.vel[1] < 0
                                 or obj.pos[1] + obj.lns >= self.termSize[0]):
                obj.vel[1] = -obj.vel[1] * self.ground.cor
                obj.pos[1] = self.termSize[0] - obj.lns + 1 - 2
    
    def start(self) -> None:
        """
        Start the engine, I guess?
        """
        fpsList: list[float]
        fpsCount   = 0
        fpsList    = []
        dataCount  = 0
        fpsListApp = fpsList.append
        lastFPS    = 0.0
        fpsTime    = time.perf_counter()
        for i in range(30000):
            # self._createMovObj(objs.Sq, f"test{i}", [2, 20], [10, 10], [0, 0], 1, 3)
            self._createMovObj(objs.Sq, f"test{i}",
                               [random.randint(1, self.termSize[1] - 1), random.randint(1, self.termSize[1] - 1)],
                               [random.randint(5, 10), random.randint(5, 10)], [0, 10], 1, 2)
        self._createTestObjs()
        self.player = self._createMovObj(objs.Player, "player",
                                         [0, self.termSize[0] - 1], [12, 12],
                                         [0, 10], 1, 2, 2, fullTxt="PLA\nYER")

        try:
            while True:
                fpsCount += 1
                self.update((now := time.perf_counter()) - self.lastTime)
                lastTimeCp    = self.lastTime
                self.lastTime = now
                self._consScr(lastFPS)

                if self.debugFPS and now - fpsTime >= 1:
                    dataCount += 1
                    fpsListApp(lastFPS := (fpsCount / (now - fpsTime)))
                    print(f"{dataCount}: {lastFPS}")
                    fpsTime            = now
                    fpsCount           = 0
                    self.roughTimeCnt += 1
                    self._createTestObjs()

                key = self.stdscr.getch()
                # No key
                if key == -1:
                    pass
                # ^C and ^Z
                elif key in (3, 26):
                    print(f"Avg. {sum(fpsList) / len(fpsList)}") \
                        if self.debugFPS else None
                    break
                # 'w', 'a', 's', 'd'
                elif key == 119:
                    self.player.vel[1] -= 1
                elif key == 97:
                    self.player.vel[0] -= 1
                elif key == 115:
                    self.player.vel[1] += 1
                elif key == 100:
                    self.player.vel[0] += 1
                # 'W', 'A', 'S', 'D'
                elif key == 87:
                    self.player.vel[1] -= 2
                elif key == 65:
                    self.player.vel[0] -= 2
                elif key == 83: 
                    self.player.vel[1] += 2
                elif key == 68:
                    self.player.vel[0] += 2
                # 'e' and 'E'
                elif key in (101, 69):
                    self.player.vel = [0.0, 0.0]
                # 'r' and 'R'
                elif key in (114, 82):
                    self.player.pos = [1.0, 1.0]
                    self.player.vel = [0.0, 0.0]
                # If the terminal window is resized
                elif key == cur.KEY_RESIZE:
                    cur.resize_term(*self.stdscr.getmaxyx())
                    self.termSize    = self.stdscr.getmaxyx()
                    self.lWall.pos   = (0, 0)
                    self.rWall.pos   = (self.termSize[1] - 1, 0)
                    self.ceiling.pos = (0, 0)
                    self.ground.pos  = (0, self.termSize[0] - 1)
                else:
                    # TODO: Remove this!
                    self.testFile.write(str(key) + '\n')

                time.sleep(max(1 / self.tgtFrameRt - (now - lastTimeCp), 0))
                self.stdscr.refresh()

        except cur.error:
            print(f"Last obj cnt = {self.roughTimeCnt * 10 + 5 + 10000}")
            self.lgr.error(tb.format_exc())

        except ZeroDivisionError:
            # For frame counter
            print("0: ?")

        except Exception:
            self.lgr.fatal(tb.format_exc())
