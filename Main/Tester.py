from shutil import rmtree, copytree, copyfile
from os.path import join, basename, exists, isdir, abspath, sep
from os import remove, listdir, mkdir
from .models import Solution, ExtraFile
from subprocess import Popen
import subprocess
from threading import Thread
from xml.dom.minidom import parse
from Sprint.settings import MEDIA_ROOT
from .main import solution_path


def shell(cmd):
    p = Popen(cmd, shell=True)
    p.wait()
    p.kill()


def start_new(host):
    in_queue = list(Solution.objects.filter(result='IN QUEUE'))
    if in_queue:
        Tester(in_queue[0], host).test()


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
        if not any(x.endswith('.exe') for x in listdir(join(path, 'bin', 'Debug'))):
            return False
        self.files.append(basename(path))
        for file in listdir(join(path, 'bin', 'Debug')):
            if exists(join(path, 'bin', 'Debug', file)):
                new_file = join(working_dir, basename(file))
                try:
                    copyfile(join(path, 'bin', 'Debug', file), new_file)
                except:
                    pass
            else:
                return False
        return True

    def push(self):
        solution = self.solution
        if solution.result == 'SOLUTION ERROR':
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
        sln_path = join(ssp, '.vs')
        if exists(sln_path):
            rmtree(sln_path)
        sln_path = ssp
        for p in listdir(sln_path):
            if isdir(join(sln_path, p)):
                if exists(join(sln_path, p, 'bin')):
                    rmtree(join(sln_path, p, 'bin'))
                if exists(join(sln_path, p, 'obj')):
                    rmtree(join(sln_path, p, 'obj'))
        if exists(self.working_dir):
            rmtree(self.working_dir)
        if exists(join(self.solution.path(), 'solution.zip')):
            remove(join(self.solution.path(), 'solution.zip'))
        if exists(join(self.solution.path(), '__MACOSX')):
            rmtree(join(self.solution.path(), '__MACOSX'))
        if exists(join(sln_path, '.DS_Store')):
            remove(join(sln_path, '.DS_Store'))
        if exists(join(sln_path, 'test_folder')):
            rmtree(join(sln_path, 'test_folder'))

    def nunit_testing(self):
        # UNIX
        # test_cmd = '(cd ' + self.working_dir + ' && ' + \
        #            'mono {} '.format(nunit_path(self.working_dir)) + \
        #            str(self.solution.task.id) + '.dll)'
        #Windows
        test_cmd = 'cd {} && mono {} '.format(self.working_dir, 'nunit3-console.exe') + str(self.solution.task.id) + '.dll'
        shell(test_cmd)
        if not exists(join(self.working_dir, 'TestResult.xml')):
            return
        try:
            doc = parse(join(self.working_dir, 'TestResult.xml'))
            tag = doc.getElementsByTagName('test-run')[0]
            passed, total = tag.getAttribute('passed'), tag.getAttribute('total')
            if not passed or not total:
                res = 'Time limit'
            else:
                res = passed + '/' + total
            self.solution.details = ''
            for el in doc.getElementsByTagName('test-case'):
                self.solution.details += '<h5><b>' + el.getAttribute('methodname') + '</b></h5>'
                r = el.getAttribute('result')
                if r == 'Passed':
                    self.solution.details += '<div style="color: green;">Passed</div>'
                else:
                    self.solution.details += '<div style="color: red;">Failed</div>'
                    mes = el.getElementsByTagName('failure')[0]
                    mes = mes.getElementsByTagName('message')[0].firstChild.nodeValue
                    self.solution.details += '<pre>{}</pre>'.format(mes)
        except:
            res = 'TEST ERROR'
        self.solution.result = res


    def test(self):
        solution = self.solution
        solution.result = 'TESTING'
        solution.save()
        try:
            if not exists(self.solution.task.tests_path()):
                solution.result = 'TEST ERROR'
                solution.save()
                self.delete_everything()
                start_new(self.host)
                return
            sln_path = solution_path(join(MEDIA_ROOT, 'solutions', str(solution.id)))
            if sln_path == '':
                solution.result = 'TEST ERROR'
                solution.save()
                self.delete_everything()
                start_new(self.host)
                return
            working_dir = join(sln_path, 'test_folder')
            if exists(working_dir):
                rmtree(working_dir)
            mkdir(working_dir)
            for project in listdir(sln_path):
                project = join(sln_path, project)
                if isdir(project) and is_project(project) and basename(project) != 'TestsProject':
                    if not self.build_and_copy(project, working_dir):
                        solution.result = 'Compilation error'
                        solution.save()
                        self.delete_everything()
                        start_new(self.host)
                        return
            dll_path = solution.task.tests_path()
            copyfile(dll_path, join(working_dir, str(solution.task.id) + '.cs'))
            for file in listdir('nunit_console'):
                try:
                    copyfile(join('nunit_console', file), join(working_dir, file))
                except:
                    pass
            self.working_dir = working_dir
            build_tests_cmd = 'csc -out:{} -t:library /r:{} /r:{} /r:{} '.format(join(self.working_dir, str(self.solution.task.id) + '.dll'), join(self.working_dir, 'nunit.framework.dll'), join(working_dir, 'System.Runtime.dll'), join(working_dir, 'DObject.dll'))
            for file in self.files:
                build_tests_cmd += '/r:{}.dll '.format(join(self.working_dir, file))
            build_tests_cmd += self.solution.task.tests_path()
            if exists(join(self.working_dir, str(self.solution.task.id) + '.dll')):
                remove(join(self.working_dir, str(self.solution.task.id) + '.dll'))
            shell(build_tests_cmd)
            if exists(join(self.working_dir, str(self.solution.task.id) + '.dll')):
                for file in ExtraFile.objects.filter(task=self.solution.task):
                    copyfile(file.path, join(working_dir, file.filename))
                thread = Thread(target=self.nunit_testing)
                thread.start()
                thread.join(solution.task.time_limit / 1000)
                if solution.result == 'TESTING':
                    solution.result = 'Time limit'
            else:
                solution.result = 'TEST ERROR'
        except:
            solution.result = 'TEST ERROR'
        solution.save()
        self.delete_everything()
        start_new(self.host)
