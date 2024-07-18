from cx_Freeze import setup, Executable

executables = [Executable('main.py')]

setup(
    name='stitchi',
    version='0.1',
    description='cli video demo',
    executables=executables
)
