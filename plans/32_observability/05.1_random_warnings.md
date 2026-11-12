# random warnings

## draft

### quitting the game

```log
W: Quitting the game

Task exception was never retrieved
future: <Task finished name='Task-1' coro=<main() done, defined at /home/pmn/repos/laife/game/main.py:79> exception=SystemExit()>
```

### pydantic

```log
/home/pmn/repos/laife/.venv/lib/python3.14/site-packages/langchain_core/_api/deprecation.py:25: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
  from pydantic.v1.fields import FieldInfo as FieldInfoV1
```

### pygame

```log
<frozen importlib._bootstrap>:491: RuntimeWarning: Your system is avx2 capable but pygame was not built with support for it. The performance of some of your blits could be adversely affected. Consider enabling compile time detection with environment variables like PYGAME_DETECT_AVX2=1 if you are compiling without cross compilation.
pygame 2.6.1 (SDL 2.0.20, Python 3.14.2)
Hello from the pygame community. https://www.pygame.org/contribute.html
```
