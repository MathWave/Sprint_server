from subprocess import Popen
from sys import stdout


def shell(cmd, output=stdout):
    p = Popen(cmd, shell=True, stdout=output)
    p.wait()
    p.kill()
