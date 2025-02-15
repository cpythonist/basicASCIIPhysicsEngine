# basicASCIIPhysicsEngine
A simple and basic ASCII physics engine written in pure Python, which supports collision with boundaries (for now), acceleration (thus emulating force) and restitution, with multi-dimensional objects.
Supply the `--help` argument for the help menu.

# Building
To build the program, you need [Nuitka](https://github.com/Nuitka/Nuitka).
## Install Nuitka-2.6.4
### Windows
```
> python -m pip install nuitka==2.6.4
```
### Linux
```
$ python3 -m pip install nuitka==2.6.4
```
## Compile the main program
After Nuitka is installed, compile `main.py` using `build.py`:
### Windows
```
> python build.py main.py <args>
```
### Linux
```
$ python3 build.py main.py <args>
```
For the help menu, use the `--help` argument.
