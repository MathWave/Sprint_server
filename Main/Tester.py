from shutil import rmtree, copytree, copyfile
from os.path import join, basename, exists, isdir, abspath, sep
from os import remove, listdir, mkdir
from .models import Solution
from subprocess import Popen
import subprocess
from threading import Thread
from xml.dom.minidom import parse


def shell(cmd):
    p = Popen(cmd, shell=True)
    p.wait()
    p.kill()


def start_new(host):
    in_queue = list(Solution.objects.filter(result='IN QUEUE'))
    if in_queue:
        Tester(in_queue[0], host).test()


def solution_path(path):
    files = [x for x in listdir(path) if '.sln' in x and not x.startswith('.')]
    if files:
        return path
    return ''.join([solution_path(join(path, file)) for file in listdir(path) if isdir(join(path, file))])


def is_project(path):
    return any([x.endswith('.csproj') for x in listdir(path)])


# функция компиляции
def build(path):
    # решение для UNIX
    # shell('msbuild ' + path + ' /p:Configuration=Debug')

    # решение для Windows
    cmd = 'dotnet build {} -o {}\\bin\\Debug'.format(path, path)
    shell(cmd)


def nunit_path(working_dir):
    return '..{}'.format(sep) * len(working_dir.split(sep)) + 'nunit_console{}nunit3-console.exe'.format(sep)


class Tester:

    def __init__(self, solution, host):
        self.solution = solution
        self.host = host
        self.working_dir = ''
        self.files = []

    def build_and_copy(self, path, working_dir):
        if exists(join(path, 'bin', 'Debug')):
            rmtree(join(path, 'bin', 'Debug'))
        build(path)
        name = basename(path)
        if not exists(join(path, 'bin', 'Debug')):
            return False
        self.files.append(basename(path))
        for file in listdir(join(path, 'bin', 'Debug')):
            if exists(join(path, 'bin', 'Debug', file)):
                new_file = join(working_dir, basename(file))
                copyfile(join(path, 'bin', 'Debug', file), new_file)
            else:
                return False
        return True

    def push(self):
        solution = self.solution
        if solution.result == 'TEST ERROR':
            return
        solution.result = 'IN QUEUE'
        solution.save()
        from Main.models import System
        if len(Solution.objects.filter(result='TESTING')) < int(System.objects.get(key='queue_size').value):
            self.test()

    def delete_everything(self):
        ssp = solution_path(self.solution.path())
        sln_path = join(ssp, '.idea')
        if exists(sln_path):
            rmtree(sln_path)
        sln_path = ssp
        for p in listdir(sln_path):
            if isdir(join(sln_path, p)):
                if exists(join(sln_path, p, 'bin')):
                    rmtree(join(sln_path, p, 'bin'))
                if exists(join(sln_path, p, 'obj')):
                    rmtree(join(sln_path, p, 'obj'))
        rmtree(self.working_dir)
        remove(join(self.solution.path(), 'solution.zip'))
        if exists(join(self.solution.path(), '__MACOSX')):
            rmtree(join(self.solution.path(), '__MACOSX'))
        if exists(join(sln_path, '.DS_Store')):
            remove(join(sln_path, '.DS_Store'))

    def nunit_testing(self):
        # UNIX
        # test_cmd = '(cd ' + self.working_dir + ' && ' + \
        #            'mono {} '.format(nunit_path(self.working_dir)) + \
        #            str(self.solution.task.id) + '.dll)'
        #Windows
        test_cmd = 'mono {} '.format(join(self.working_dir, 'nunit3-console.exe')) + \
                   '--work {} '.format(self.working_dir) + join(self.working_dir, str(self.solution.task.id)) + '.dll'
        shell(test_cmd)
        with open('log1.txt', 'w') as fs:
            fs.write(test_cmd)
       # p = Popen(test_cmd, shell=True)
       # p.wait(self.solution.task.time_limit)
       # p.kill()
        doc = parse(join(self.working_dir, 'TestResult.xml'))
        tag = doc.getElementsByTagName('test-run')[0]
        passed, total = tag.getAttribute('passed'), tag.getAttribute('total')
        if not passed or not total:
            res = 'Time limit'
        else:
            res = passed + '/' + total
        self.solution.result = res


    def test(self):
        solution = self.solution
        solution.result = 'TESTING'
        solution.save()
        if not exists(self.solution.task.tests_path()):
            solution.result = 'TEST ERROR'
            solution.save()
            self.delete_everything()
            start_new(self.host)
            return
        sln_path = solution_path(join('C:\\Users\\nchuykin\\data', 'solutions', str(solution.id)))
        working_dir = join(sln_path, 'test_folder')
        mkdir(working_dir)
        for project in listdir(sln_path):
            project = join(sln_path, project)
            
            if isdir(project) and is_project(project):
                if not self.build_and_copy(project, working_dir):
                    solution.result = 'Compilation error'
                    solution.save()
                    self.delete_everything()
                    start_new(self.host)
                    return
        dll_path = solution.task.tests_path()
        copyfile(dll_path, join(working_dir, str(solution.task.id) + '.dll'))
        for file in listdir('nunit_console'):
            try:
                copyfile(join('nunit_console', file), join(working_dir, file))
            except:
                pass
        self.working_dir = working_dir
        build_tests_cmd = 'csc -out:{} -t:library /r:{} /r:{} '.format(join(self.working_dir, str(self.solution.task.id) + '.dll'), join(self.working_dir, 'nunit.framework.dll'), join(working_dir, 'System.Runtime.dll'))
        for file in self.files:
            build_tests_cmd += '/r:{}.dll '.format(join(self.working_dir, file))
        build_tests_cmd += self.solution.task.tests_path()
        print(build_tests_cmd)
        shell(build_tests_cmd)
        thread = Thread(target=self.nunit_testing)
        thread.start()
        thread.join(solution.task.time_limit / 1000)
        if solution.result == 'TESTING':
            solution.result = 'Time limit'
        solution.save()
        self.delete_everything()
        start_new(self.host)