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
from sys import stdout


def shell(cmd, output=stdout):
    p = Popen(cmd, shell=True, stdout=output)
    p.wait()
    p.kill()


def start_new(host):
    in_queue = list(Solution.objects.filter(result='IN QUEUE'))
    if in_queue:
        Tester(in_queue[0], host).test()


def is_project(path):
    return any([x.endswith('.csproj') for x in listdir(path)])


def get_node_value(element):
    return element[0].firstChild.nodeValue


def nunit_path(working_dir):
    return '..{}'.format(sep) * len(working_dir.split(sep)) + 'nunit_console{}nunit3-console.exe'.format(sep)


class Tester:

    def __init__(self, solution, host):
        self.solution = solution
        self.host = host
        self.working_dir = ''
        self.files = []

    # функция компиляции
    def build(self, path):
        # решение для UNIX
        # shell('msbuild ' + path + ' /p:Configuration=Debug')

        # решение для Windows
        cmd = 'dotnet build {} -o {}\\bin\\Debug'.format(path, path)
        with self.solution.log_fs as fs:
            shell(cmd, fs)

    def build_and_copy(self, path, working_dir):
        if exists(join(path, 'bin', 'Debug')):
            rmtree(join(path, 'bin', 'Debug'))
        self.build(path)
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
        solution = self.solution
        with self.solution.log_fs as fs:
            fs.write(b'Building image\n')
        shell('docker build -t solution_{} {}'.format(self.solution.id, self.working_dir))
        with self.solution.log_fs as fs:
            fs.write(b'Image built successfully\n')
        def execute():
            with self.solution.log_fs as fs:
                shell('docker run --name solution_container_{} solution_{}'.format(self.solution.id, self.solution.id), output=fs)
        solution.write_log('Running container')
        t = Thread(target=execute)
        t.start()
        t.join(self.solution.task.time_limit / 1000)
        solution.write_log('Running finished')
        with self.solution.log_fs as fs:
            shell('docker cp solution_container_{}:/app/TestResults.xml {}'.format(self.solution.id, self.working_dir), fs)
        with self.solution.log_fs as fs:
            shell('docker rm --force solution_container_{}'.format(self.solution.id), fs)
        with self.solution.log_fs as fs:
            shell('docker image rm solution_{}'.format(self.solution.id), fs)
        if not exists(join(self.working_dir, 'TestResults.xml')):
            self.solution.set_result('Time limit')
            solution.write_log('Result file not found in container')
            return
        solution.write_log('Result file found in container')
        try:
            doc = parse(join(self.working_dir, 'TestResults.xml'))
            res = get_node_value(doc.getElementsByTagName('Passed')) + '/' + get_node_value(doc.getElementsByTagName('Total'))
            self.solution.details = ''
            for el in doc.getElementsByTagName('Result'):
                self.solution.details += '<h5><b>' + get_node_value(el.getElementsByTagName('MethodName')) + '</b></h5>'
                r = get_node_value(el.getElementsByTagName('Successful'))
                if r == 'true':
                    self.solution.details += '<div style="color: green;">Passed</div>'
                else:
                    self.solution.details += '<div style="color: red;">Failed</div>'
                    mes = get_node_value(el.getElementsByTagName('Message'))
                    self.solution.details += '<pre>{}</pre>'.format(mes)
        except:
            solution.write_log('Unknown error')
            res = 'TEST ERROR'
        self.solution.set_result(res)


    def test(self):
        solution = self.solution
        solution.result = 'TESTING'
        solution.save()
        try:
            if not exists(self.solution.task.tests_path()):
                with self.solution.log_fs as fs:
                    fs.write(b'No test file found\n')
                solution.set_result('TEST ERROR')
                solution.save()
                self.delete_everything()
                start_new(self.host)
                return
            sln_path = solution_path(join(MEDIA_ROOT, 'solutions', str(solution.id)))
            if sln_path == '':
                solution.set_result('TEST ERROR')
                solution.save()
                self.delete_everything()
                start_new(self.host)
                return
            working_dir = join(sln_path, 'test_folder')
            if exists(working_dir):
                rmtree(working_dir)
            mkdir(working_dir)
            with self.solution.log_fs as fs:
                fs.write(b'Testing directory created\n')
            for project in listdir(sln_path):
                solution.write_log('Checking if {} is project'.format(project))
                prj = project
                project = join(sln_path, project)
                if isdir(project) and is_project(project) and basename(project) != 'TestsProject':
                    if not self.build_and_copy(project, working_dir):
                        solution.set_result('Compilation error')
                        solution.write_log('Failed to compile project {}'.format(prj))
                        solution.save()
                        self.delete_everything()
                        start_new(self.host)
                        return
            dll_path = solution.task.tests_path()
            with self.solution.log_fs as fs:
                fs.write(b'Copying test file to working directory\n')
            copyfile(dll_path, join(working_dir, str(solution.task.id) + '.cs'))
            with self.solution.log_fs as fs:
                fs.write(b'Test file copied\n')
            for file in listdir('SprintTest'):
                try:
                    copyfile(join('SprintTest', file), join(working_dir, file))
                except:
                    pass
            self.working_dir = working_dir
            build_tests_cmd = 'csc -out:{} -t:library /r:{} /r:{} /r:{} '.format(join(self.working_dir, 'tests.dll'), join(self.working_dir, 'SprintTest.dll'), join(working_dir, 'System.Runtime.dll'), join(working_dir, 'System.Reflection.dll'))
            for file in self.files:
                build_tests_cmd += '/r:{}.dll '.format(join(self.working_dir, file))
            build_tests_cmd += self.solution.task.tests_path()
            if exists(join(self.working_dir, 'tests.dll')):
                remove(join(self.working_dir, 'tests.dll'))
            with self.solution.log_fs as fs:
                fs.write(b'Building tests file started\n')
            with self.solution.log_fs as fs:
                shell(build_tests_cmd, fs)
            with self.solution.log_fs as fs:
                fs.write(b'Building tests file finished\n')
            if exists(join(self.working_dir, 'tests.dll')):
                with self.solution.log_fs as fs:
                    fs.write(b'Got .dll tests file\n')
                for file in ExtraFile.objects.filter(task=self.solution.task):
                    copyfile(file.path, join(working_dir, file.filename))
                self.nunit_testing()
            else:
                solution.set_result('TEST ERROR')
                with self.solution.log_fs as fs:
                    fs.write(b'Failed to compile tests\n')
        except:
            solution.set_result('TEST ERROR')
            raise
            with self.solution.log_fs as fs:
                fs.write(b'Unknown error\n')
        solution.save()
        self.delete_everything()
        start_new(self.host)
