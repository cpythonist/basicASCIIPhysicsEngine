class BaseObj:
    def __init__(self, name: str):
        self.name = name
        self.txt  = ''
        self.lns   = 0
        self.cols  = 0


class MovableObj(BaseObj):
    def __init__(self, name: str, pos: list[float], vel: list[float],
                 accl: list[float], cor: float, char: str = '#',
                 invis: bool = False) -> None:
        super().__init__(name)
        self.pos   = pos
        self.vel   = vel
        self.accl  = accl
        self.cor   = cor
        self.char  = char
        self.invis = invis
    
    def __str__(self) -> str:
        return f"MovableObj({self.name}, {self.pos}, {self.vel}, {self.accl})"


class ImmovableObj(BaseObj):
    def __init__(self, name: str, pos: tuple[float, float], cor: float,
                 char: str = '#', invis: bool = False) -> None:
        super().__init__(name)
        self.pos   = pos
        self.cor   = cor
        self.char  = char
        self.invis = invis
    
    def __str__(self) -> str:
        return f"ImmovableObj({self.name}, {self.pos})"


class BoundaryObj(ImmovableObj):
    def __init__(self, name: str, pos: tuple[float, float], size: int,
                 cor: float, char: str = '#', invis: bool = False) -> None:
        super().__init__(name, pos, cor, char, invis)
        self.size = size


class Sq(MovableObj):
    def __init__(self, name: str, pos: list[float], vel: list[float],
                 accl: list[float], cor: float, side: int, char: str = '#',
                 invis: bool = False) -> None:
        super().__init__(name, pos, vel, accl, cor, char, invis)
        self.side = side
        self.txt  = '\n'.join([self.char * self.side for _ in range(self.side)])
        self.lns  = len(self.txt.splitlines())
        self.cols = max([len(i) for i in self.txt.splitlines()])


class Diamond(MovableObj):
    def __init__(self, name: str, pos: list[float], vel: list[float],
                    accl: list[float], cor: float, ht: int, char: str = '#',
                    invis: bool = False) -> None:
        super().__init__(name, pos, vel, accl, cor, char, invis)
        lines: list[str]
        self.ht = ht
        lines   = []
        # TODO: Getting real irritated... See this later!
        for i in range(self.ht // 2):
            lines.append(' ' * (self.ht - 2 * i) + self.char * (2 * i + 1))
        lines.extend([self.char * self.ht] + lines[::-1])
        print('\n'.join(lines))


class InternalWall(ImmovableObj):
    def __init__(self, name: str, pos: tuple[float, float], cor: float,
                 wd: int, ht: int, char: str = '#',
                 invis: bool = False) -> None:
        super().__init__(name, pos, cor, char, invis)
        self.wd  = wd
        self.ht  = ht
        self.txt = '\n'.join([self.char * self.wd for _ in range(self.ht)])


class Player(MovableObj):
    def __init__(self, name: str, pos: list[float], vel: list[float],
                 accl: list[float], cor: float, wd: int, ht: int,
                 char: str = '@', fullTxt: str = '',
                 invis: bool = False) -> None:
        super().__init__(name, pos, vel, accl, cor, char, invis)
        self.char    = char
        self.txt     = ('\n'.join([self.char * wd for _ in range(ht)])
                        if not fullTxt else fullTxt)
        self.lns     = len(self.txt.splitlines())
        self.cols    = max([len(i) for i in self.txt.splitlines()])
        self.health  = 100


# Diamond('test', [0, 0], [0, 0], [0, 0], ht=5)
