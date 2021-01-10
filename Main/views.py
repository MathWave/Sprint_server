from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse, FileResponse
from django.shortcuts import render
from django.core.files import File
from .forms import *
from django.contrib.auth import login, authenticate, logout
from django.utils import timezone
from datetime import datetime
import datetime as dt
from django.utils.timezone import make_aware
from zipfile import ZipFile, BadZipFile
from threading import Thread
from os import remove, mkdir, listdir, rename
from os.path import exists
from json import load, dumps, loads
from .Tester import Tester, shell
from .main import solutions_filter, check_admin_on_course, re_test, check_admin, check_teacher, random_string, \
    send_email, check_permission_block, is_integer, check_god, blocks_available, check_login, \
    get_restore_hash, block_solutions_info, delete_folder, solution_path, can_send_solution, get_in_html_tag
from .models import System, Solution, Block, Subscribe, Course, UserInfo, Task, Restore, ExtraFile
from os.path import sep, join, exists, isfile, dirname
from shutil import rmtree, copytree, make_archive, copyfile
from Sprint.settings import MEDIA_ROOT


def download(request):
    if not check_admin(request.user) or not check_admin_on_course(request.user, Block.objects.get(id=request.GET['block_id']).course):
        return HttpResponseRedirect('/main')
    sols = solutions_filter(request.GET)
    if len(sols) == 0:
        return HttpResponseRedirect('/admin/solutions?block_id=' + request.GET['block_id'])
    new_folder = join(MEDIA_ROOT, request.user.username)
    if exists(new_folder):
        rmtree(new_folder)
    mkdir(new_folder)
    cur_folder = join(new_folder, 'solutions')
    mkdir(cur_folder)
    for sol in sols:
        copytree(join(MEDIA_ROOT, 'solutions', str(sol.id)), join(cur_folder, str(sol.id)))
    zip_folder = join(dirname(cur_folder), 'solutions')
    make_archive(zip_folder, 'zip', cur_folder)
    response = HttpResponse(open(zip_folder + '.zip', 'rb').read(), content_type='application/force-download')
    response['Content-Disposition'] = 'inline; filename=solutions.zip'
    rmtree(dirname(cur_folder))
    return response


def docs(request):
    if not check_admin(request.user):
        return HttpResponseRedirect('/main')
    return render(request, "docs.html", context={'is_teacher': check_teacher(request.user)})


def retest(request):
    solutions_request = solutions_filter(request.GET)
    if not check_admin_on_course(request.user, Block.objects.get(id=request.GET['block_id']).course):
        return HttpResponseRedirect('/main')
    req = '?block_id=' + str(request.GET['block_id'])
    for key in request.GET.keys():
        if key != 'block_id':
            req += '&{}={}'.format(key, request.GET[key])
    Thread(target=lambda: re_test(solutions_request, request)).start()
    if 'next' in request.GET.keys():
        return HttpResponseRedirect(request.GET['next'])
    return HttpResponseRedirect('/admin/solutions%s' % req)


def solution(request):
    current_solution = Solution.objects.get(id=request.GET['id'])
    try:
        Subscribe.objects.get(user=request.user, course=current_solution.task.block.course)
    except ObjectDoesNotExist:
        if not request.user.is_superuser:
            return HttpResponseRedirect('/main')
    can_edit = check_admin_on_course(request.user, current_solution.task.block.course)
    if not can_edit:
        # тут по хорошему надо использовать регулярки, но я что-то не разобрался
        while True:
            i = current_solution.details.find('<pre>')
            if i == -1:
                break
            j = current_solution.details.find('</pre>') + 6
            current_solution.details = current_solution.details.replace(current_solution.details[i:j], '')
        if current_solution.user != request.user:
            return HttpResponseRedirect('/main')
    solutions_request = solutions_filter(request.GET)
    if request.path == '/admin/solution':
        from_admin = True
    else:
        from_admin = False
    if request.method == 'POST' and can_edit:
        if request.POST['action'] == 'Зачесть':
            current_solution.mark = None if request.POST['mark'] == 'нет оценки' else int(request.POST['mark'])
        elif request.POST['action'] == 'Незачесть':
            current_solution.mark = 0
        else:
            current_solution.mark = current_solution.task.max_mark
        current_solution.comment = request.POST['comment']
        current_solution.save()
    return render(request, 'solution.html', context={'solution': current_solution,
                                                     'from_admin': from_admin,
                                                     'can_edit': can_edit,
                                                     'path': request.path})


def solutions(request):
    current_block = Block.objects.get(id=request.GET['block_id'])
    try:
        if not request.user.is_superuser:
            s = Subscribe.objects.get(user=request.user, course=current_block.course)
            if not s.is_assistant and not s.user.is_staff:
                return HttpResponseRedirect('/main')
    except ObjectDoesNotExist:
        return HttpResponseRedirect('/main')
    req = ''
    sols = solutions_filter(request.GET)
    for key in request.GET.keys():
        req += '&{}={}'.format(key, request.GET[key])
    if request.method == 'POST':
        Solution.objects.get(id=request.POST['DELETE_SOLUTION']).delete()
        return HttpResponseRedirect('/admin/solutions?block_id={}{}'.format(current_block.id, req))
    return render(request, 'solutions.html', context={'Block': current_block,
                                                      'filter': ' '.join([str(sol.id) for sol in sols]),
                                                      'solutions': sols,
                                                      'req': req,
                                                      'options': {key: request.GET[key] for key in request.GET.keys()},
                                                      'solutions_info': block_solutions_info(current_block)})


def users_settings(request):
    current_course = Course.objects.get(id=request.GET['course_id'])
    if not check_teacher(request.user):
        return HttpResponseRedirect('/main')
    try:
        Subscribe.objects.get(user=request.user, course=current_course)
    except ObjectDoesNotExist:
        if not request.user.is_superuser:
            return HttpResponseRedirect('/main')
    if request.method == 'POST':
        if 'input' in request.POST.keys():
            line = request.POST['input']
            if '@' in line:
                users = UserInfo.objects.filter(user__email=line)
            elif any(c.isdigit() for c in line) or line == '-':
                users = UserInfo.objects.filter(group=line)
            else:
                try:
                    s, n, m = line.split(' ')
                except ValueError:
                    s, n, m = '', '', ''
                users = UserInfo.objects.filter(surname=s, name=n, middle_name=m)
            for user in users:
                try:
                    Subscribe.objects.get(user=user.user, course=current_course)
                except ObjectDoesNotExist:
                    Subscribe.objects.create(user=user.user, course=current_course)
        elif 'user_delete' in request.POST.keys():
            username = request.POST['user_delete']
            course_id = request.GET['course_id']
            Subscribe.objects.get(user__email=username, course_id=course_id).delete()
        elif 'file' in request.FILES.keys():
            users = load(request.FILES['file'])
            for u in users:
                password = random_string()
                flag = False
                try:
                    User.objects.get(email=u['email'])
                except ObjectDoesNotExist:
                    flag = True
                if flag:
                    user = User.objects.create_user(username=u['email'],
                                                    email=u['email'],
                                                    password=password)
                    UserInfo.objects.create(
                        surname=u['surname'],
                        name=u['name'],
                        middle_name=u['middle_name'],
                        group=u['group'],
                        user=user
                    )
                    Subscribe.objects.create(user=user, course=current_course, is_assistant=False)
                    send_email('You have been registered in Sprint!', u['email'],
                               'Your password is: {}\nPlease change it after login in settings!'.format(password))
        else:
            username = request.POST['user']
            s = Subscribe.objects.get(user__email=username, course=current_course)
            s.is_assistant = not s.is_assistant
            s.save()
    return render(request, 'users_settings.html', context={'course': current_course})


def task(request):
    current_task = Task.objects.get(id=request.GET['id'])
    user = request.user
    if not check_permission_block(user, current_task.block):
        return HttpResponseRedirect('/main')
    can_send = can_send_solution(user, current_task)
    if request.method == 'POST':
        if 'file' in request.FILES.keys() and can_send:
            current_solution = Solution.objects.create(
                task=current_task,
                user=request.user,
                result='IN QUEUE',
                time_sent=timezone.now()
            )
            log_file_path = current_solution.log_file
            with open(log_file_path, 'wb') as fs:
                pass
            solution_dir = current_solution.path() + sep
            if exists(solution_dir):
                rmtree(solution_dir)
            mkdir(solution_dir)
            with open(solution_dir + 'solution.zip', 'wb') as fs:
                for chunk in request.FILES['file'].chunks():
                    fs.write(chunk)
            flag = False
            solution_created = False
            try:
                with ZipFile(solution_dir + 'solution.zip') as obj:
                    obj.extractall(solution_dir)
            except BadZipFile:
                rename(solution_dir + 'solution.zip', solution_dir + request.FILES['file'].name)
            sln_path = solution_path(solution_dir)
            if current_task.full_solution != bool(sln_path):
                current_solution.result = 'TEST ERROR'
                with open(log_file_path, 'ab') as fs:
                    fs.write(b'Can\'t find sln file in solution' if current_task.full_solution else b'Sln file in path')                        
                current_solution.save()
                return HttpResponseRedirect('/task?id=' + str(current_task.id))
            if not bool(sln_path):
                copytree('SampleSolution', join(solution_dir, 'Solution'))
                for file in listdir(solution_dir):
                    if file == 'solution.zip' or file == 'Solution':
                        continue
                    cur_file = join(solution_dir, file)
                    if isfile(cur_file):
                        copyfile(cur_file, join(solution_dir, 'Solution', 'SampleProject', file))
                        remove(cur_file)
                    else:
                        rmtree(cur_file)
            if not current_task.full_solution:
                for file in current_task.files_for_compilation:
                    copyfile(file.path, join(solution_dir, 'Solution', 'SampleProject', file.filename))
            #Tester(current_solution, request.META['HTTP_HOST']).push()
            Thread(target=lambda: Tester(current_solution, request.META['HTTP_HOST']).push()).start()
            return HttpResponseRedirect('/task?id=' + str(current_task.id))
    return render(request, 'task.html', context={'task': current_task,
                                                 'solutions': reversed(Solution.objects.filter(task=current_task, user=user)),
                                                 'can_send': can_send,
                                                 'can_edit': check_admin_on_course(request.user, current_task.block.course)})


from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def task_test(request):
    current_task = Task.objects.get(id=request.GET['id'])
    user = request.user
    if not check_permission_block(user, current_task.block):
        return HttpResponseRedirect('/main')
    can_send = can_send_solution(user, current_task)
    if request.method == 'POST':
        if 'file' in request.FILES.keys() and can_send:
            current_solution = Solution.objects.create(
                task=current_task,
                user=request.user,
                result='IN QUEUE',
                time_sent=timezone.now()
            )
            log_file_path = current_solution.log_file
            with open(log_file_path, 'wb') as fs:
                pass
            solution_dir = current_solution.path() + sep
            if exists(solution_dir):
                rmtree(solution_dir)
            mkdir(solution_dir)
            with open(solution_dir + 'solution.zip', 'wb') as fs:
                for chunk in request.FILES['file'].chunks():
                    fs.write(chunk)
            flag = False
            solution_created = False
            try:
                with ZipFile(solution_dir + 'solution.zip') as obj:
                    obj.extractall(solution_dir)
            except BadZipFile:
                rename(solution_dir + 'solution.zip', solution_dir + request.FILES['file'].name)
            sln_path = solution_path(solution_dir)
            if current_task.full_solution != bool(sln_path):
                current_solution.result = 'TEST ERROR'
                with open(log_file_path, 'ab') as fs:
                    fs.write(b'Can\'t find sln file in solution' if current_task.full_solution else b'Sln file in path')                        
                current_solution.save()
                return HttpResponseRedirect('/task?id=' + str(current_task.id))
            if not bool(sln_path):
                copytree('SampleSolution', join(solution_dir, 'Solution'))
                for file in listdir(solution_dir):
                    if file == 'solution.zip' or file == 'Solution':
                        continue
                    cur_file = join(solution_dir, file)
                    if isfile(cur_file):
                        copyfile(cur_file, join(solution_dir, 'Solution', 'SampleProject', file))
                        remove(cur_file)
                    else:
                        rmtree(cur_file)
            if not current_task.full_solution:
                for file in current_task.files_for_compilation:
                    copyfile(file.path, join(solution_dir, 'Solution', 'SampleProject', file.filename))
            #Tester(current_solution, request.META['HTTP_HOST']).push()
            Thread(target=lambda: Tester(current_solution, request.META['HTTP_HOST']).push()).start()
            return HttpResponseRedirect('/task?id=' + str(current_task.id))


def block(request):
    current_block = Block.objects.get(id=request.GET['id'])
    if not check_permission_block(request.user, current_block):
        return HttpResponseRedirect('/main')
    return render(request, 'block.html', context={'Block': current_block,
                                                  'is_admin': check_admin(request.user),
                                                  'can_edit': check_admin_on_course(request.user, current_block.course),
                                                  'user': request.user})


def task_settings(request):
    if not check_admin(request.user):
        return HttpResponseRedirect('/main')
    current_task = Task.objects.get(id=request.GET['id'])
    if request.method == 'POST':
        action = request.POST['ACTION']
        if action == 'DELETE':
            t = Task.objects.get(id=request.GET['id'])
            block_id = t.block.id
            t.delete()
            return HttpResponseRedirect('/admin/block?id=' + str(block_id))
        elif action.startswith('SAVE_EXTRA_FILE_'):
            i = action.split('_')[-1]
            ef = ExtraFile.objects.get(id=int(i))
            with open(ef.path, 'wb') as fs:
                fs.write(bytes(request.POST['extra_file_text_' + i], encoding='utf-8'))
            ef.for_compilation = '{}_for_compilation'.format(ef.id) in request.POST.keys()
            ef.save()
        elif action == 'SAVE':
            current_task.legend, current_task.input, current_task.output, current_task.specifications = \
            request.POST['legend'],  request.POST['input'], request.POST['output'], request.POST['specifications']
            current_task.time_limit = int(request.POST['time_limit']) if is_integer(request.POST['time_limit']) else 10000
            current_task.show_details = 'show_details' in request.POST.keys()
            current_task.full_solution = 'full_solution' in request.POST.keys()
            current_task.mark_formula = request.POST['mark_formula']
            current_task.show_result = 'show_result' in request.POST.keys()
            for ef in ExtraFile.objects.filter(task=current_task):
                ef.sample = 'sample_' + str(ef.id) in request.POST.keys()
                ef.save()
            try:
                current_task.weight = float(request.POST['weight'].replace(',', '.'))
            except ValueError:
                current_task.weight = 1.0
            try:
                current_task.max_mark = int(request.POST['max_mark'])
                if current_task.max_mark == 0:
                    raise ValueError
            except ValueError:
                current_task.max_mark = 10
            try:
                current_task.max_solutions_count = int(request.POST['max_solutions_count'])
            except ValueError:
                current_task.max_solutions_count = 10

        elif action == 'UPLOAD_EXTRA_FILE':
            if request.FILES['file'].name.endswith('.zip'):
                try:
                    wdir = join(MEDIA_ROOT, 'extra_files', 'files' + str(current_task.id))
                    if exists(wdir):
                        rmtree(wdir)
                    mkdir(wdir)
                    with open(join(wdir, 'file.zip'), 'wb') as fs:
                        for chunk in request.FILES['file'].chunks():
                            fs.write(chunk)
                    with ZipFile(join(wdir, 'file.zip')) as obj:
                        obj.extractall(wdir)
                    remove(join(wdir, 'file.zip'))
                    for file in listdir(wdir):
                        if isfile(join(wdir, file)):
                            try:
                                ef = ExtraFile.objects.get(filename=file, task=current_task)
                            except ObjectDoesNotExist:
                                ef = ExtraFile.objects.create(filename=file, task=current_task)
                            ef.write(open(join(wdir, file), 'rb').read().strip())
                    rmtree(wdir)
                except BadZipFile:
                    pass
            else:
                try:
                    ef = ExtraFile.objects.get(filename=request.FILES['file'].name, task=current_task)
                except ObjectDoesNotExist:
                    ef = ExtraFile.objects.create(filename=request.FILES['file'].name, task=current_task)
                with open(ef.path, 'wb') as fs:
                    for chunk in request.FILES['file'].chunks():
                        fs.write(chunk)
        elif action == 'CREATE_EXTRA_FILE':
            try:
                ExtraFile.objects.get(task=current_task, filename=request.POST['newfile_name'])
            except ObjectDoesNotExist:
                ef = ExtraFile.objects.create(task=current_task, filename=request.POST['newfile_name'])
                f = open(join(MEDIA_ROOT, 'extra_files', str(ef.id)), 'w')
                f.close()
        elif action.startswith('DELETE_FILE_'):
            ExtraFile.objects.get(id=int(action.split('_')[-1])).delete()
        elif action == 'SAVE_TESTS':
            tt = request.POST['tests_text']
            cs_file = current_task.tests_path()
            with open(cs_file, 'wb') as fs:
                fs.write(bytes(tt, encoding='utf-8'))
            for ef in ExtraFile.objects.filter(task=current_task):
                ef.write(bytes(request.POST['extra_file_text_{}'.format(ef.id)], encoding='utf-8'))
                ef.for_compilation = str(ef.id) + '_for_compilation' in request.POST.keys()
                ef.save()
        else:
            raise NotImplementedError()
        current_task.save()
        return HttpResponseRedirect('/admin/task?id=' + str(current_task.id))
    return render(request, 'task_settings.html', context={'task': current_task,
                                                          'tests': TestsForm(),
                                                          'is_superuser': check_teacher(request.user)})


def block_settings(request):
    if not check_admin(request.user):
        return HttpResponseRedirect('/main')
    current_block = Block.objects.get(id=request.GET['id'])
    if not check_permission_block(request.user, current_block):
        return HttpResponseRedirect('/main')
    if request.method == 'POST':
        if 'name' in request.POST.keys():
            current_block = Block.objects.get(id=request.POST['block_id'])
            if not check_teacher(request.user) or not check_permission_block(request.user, current_block):
                return HttpResponseRedirect('/main')
            task_name = request.POST['name']
            current_task = Task.objects.create(
                name=task_name,
                block=current_block
            )
            with open(current_task.tests_path(), 'w') as fs:
                pass
            return HttpResponseRedirect('/admin/task?id=' + str(current_task.id))
        if 'file' in request.FILES.keys():
            if exists(request.user.username):
                rmtree(request.user.username)
            mkdir(request.user.username)
            with open(join(request.user.username, 'task.zip'), 'wb') as fs:
                for chunk in request.FILES['file'].chunks():
                    fs.write(chunk)
            try:
                with ZipFile(join(request.user.username, 'task.zip')) as obj:
                    obj.extractall(request.user.username)
            except BadZipFile:
                rmtree(request.user.username)
                return HttpResponseRedirect('/admin/block?id={}'.format(current_block.id))
            task = Task.objects.create(name='Новый таск', block=current_block)
            root = request.user.username
            if exists(join(root, 'meta.json')):
                data = loads(open(join(root, 'meta.json'), 'r', encoding='utf-8').read())
                task.name = data['localizedNames']['ru']
                task.time_limit = data['invocationLimits']['idlenessLimitMillis']
                for f in sorted(listdir(join(root, 'tests'))):
                    e = ExtraFile.objects.create(
                        task=task,
                        filename=f,
                        for_compilation=False
                    )
                    try:
                        e.sample=data['testSets'][str(int(f.split('.')[0]))]['example'] and not f.endswith('.a')
                    except KeyError:
                        e.sample = False
                    e.save()
                    copyfile(join(root, 'tests', f), join(MEDIA_ROOT, 'extra_files', str(e.id)))
                statements = open(join(root, 'statements', 'ru', 'html', 'statement.html'), 'r', encoding='utf-8').read()
                task.legend = get_in_html_tag(statements, 'legend')
                task.input = get_in_html_tag(statements, 'input-specification')
                task.output = get_in_html_tag(statements, 'output-specification')
                task.specifications = get_in_html_tag(statements, 'notes')
                task.save()
                with open(join(MEDIA_ROOT, 'tests', str(task.id) + '.cs'), 'w') as fs:
                    pass
                rmtree(root)
                return HttpResponseRedirect('/admin/task?id={}'.format(task.id))
        if 'block_delete' in request.POST.keys():
            Block.objects.get(id=request.POST['block_delete']).delete()
            return HttpResponseRedirect('/admin/main')
        else:
            time_start = make_aware(datetime.strptime(request.POST['time_start'], "%Y-%m-%dT%H:%M") + dt.timedelta(hours=3))
            time_end = make_aware(datetime.strptime(request.POST['time_end'], "%Y-%m-%dT%H:%M") + dt.timedelta(hours=3))
            current_block.opened = 'opened' in request.POST.keys()
            current_block.time_start = time_start
            current_block.time_end = time_end
            current_block.show_rating = "rating" in request.POST.keys()
            current_block.save()
            return HttpResponseRedirect('/admin/block?id={}'.format(current_block.id))
    return render(request, 'block_settings.html', context={'is_superuser': check_teacher(request.user),
                                                           'Block': current_block})


def solutions_table(request):
    current_task = Task.objects.get(id=request.GET['id'])
    user = request.user
    if not check_permission_block(user, current_task.block):
        return HttpResponse("done")
    sols = Solution.objects.filter(task=current_task, user=user)          
    can_edit = check_admin_on_course(request.user, current_task.block.course)
    # тут по хорошему надо использовать регулярки, но я что-то не разобрался
    if not can_edit:
        for sol in sols:
            while True:
                i = sol.details.find('<pre>')
                if i == -1:
                    break
                j = sol.details.find('</pre>') + 6
                sol.details = sol.details.replace(sol.details[i:j], '')
    if any(sol.result == 'TESTING' or sol.result == 'IN QUEUE' for sol in sols) or 'render' in request.GET.keys():
        return render(request, 'solutions_table.html', context={ 
            'solutions': reversed(sols),
            'can_edit': can_edit,
            'task': current_task})
    return HttpResponse('done')


def get_result_data(request):
    solution = Solution.objects.get(id=request.GET['id'])
    if not check_admin_on_course(request.user, solution.task.block.course):
        return HttpResponse(dumps({'success': False}))
    return HttpResponse(dumps({
        'success': True,
        'results_text': solution.details,
        'tests_text': solution.task.tests_text,
        'log_text': solution.log_text
    }))


def get_comment_data(request):
    solution = Solution.objects.get(id=request.GET['id'])
    if not check_admin_on_course(request.user, solution.task.block.course):
        return HttpResponse(dumps({'success': False}))
    return HttpResponse(dumps({
        'success': True,
        'comment_text': solution.comment
    }))

    
def rating(request):
    current_block = Block.objects.get(id=request.GET['block_id'])
    if not check_admin_on_course(request.user, current_block.course) and not current_block.show_rating:
        return HttpResponseRedirect('/main')
    return render(request, 'rating.html', context={'Block': Block.objects.get(id=request.GET['block_id'])})


def admin(request):
    if not check_admin(request.user):
        return HttpResponseRedirect('/main')
    if request.method == 'POST':
        course = Course.objects.get(id=request.POST['course_id'])
        if not check_teacher(request.user):
            return HttpResponseRedirect('/main')
        try:
            Subscribe.objects.get(user=request.user, course=course)
        except ObjectDoesNotExist:
            if not request.user.is_superuser:
                return HttpResponseRedirect('/main')
        name = request.POST['name']
        current_block = Block.objects.create(name=name,
                                             course=course,
                                             opened=False,
                                             time_start=timezone.now(),
                                             time_end=timezone.now())
        return HttpResponseRedirect('/admin/block?id=' + str(current_block.id))
    return render(request, "admin.html", context={"blocks": blocks_available(request.user),
                                                  'is_superuser': check_god(request.user),
                                                  'is_teacher': check_teacher(request.user)})


def reset_password(request):
    code = request.GET['code']
    try:
        res = Restore.objects.get(code=code)
    except ObjectDoesNotExist:
        return HttpResponseRedirect('/enter')
    context = {'form': ResetPasswordForm()}
    if request.method == 'GET':
        return render(request, 'reset_password.html', context=context)
    else:
        if request.POST['new'] != request.POST['again']:
            context['error'] = 'Пароли не совпадают'
            return render(request, 'reset_password.html', context=context)
        else:
            res.user.set_password(request.POST['new'])
            res.user.save()
            res.delete()
            return HttpResponseRedirect('/enter')


def settings(request):
    if not check_login(request.user):
        return HttpResponseRedirect('/enter')
    context = {'is_admin': check_admin(request.user), 'form': ChangePasswordForm()}
    if request.method == 'POST':
        old = request.POST['old']
        new = request.POST['new']
        again = request.POST['again']
        username = request.user.username
        user = authenticate(username=username, password=old)
        if user is None:
            context['error'] = 'Неверный пароль'
        elif new != again:
            context['error'] = 'Пароли не совпадают'
        elif new == '' or new.replace(' ', '') == '':
            context['error'] = 'Некорректный пароль'
        else:
            user.set_password(new)
            user.save()
            context['error'] = 'Пароль успешно изменен'
            user = authenticate(username=username, password=new)
            if user is not None and user.is_active:
                login(request, user)
    return render(request, 'settings.html', context=context)


def exit(request):
    logout(request)
    return HttpResponseRedirect('/enter')


def redirect(request):
    return HttpResponseRedirect('/main')


def main(request):
    if not check_login(request.user):
        return HttpResponseRedirect('/enter')
    return render(request, 'main.html', context={'blocks': blocks_available(request.user)})


def restore(request):
    if check_login(request.user):
        return HttpResponseRedirect('/main')
    elif request.method == 'GET':
        return render(request, 'restore.html')
    else:
        email = request.POST['email']
        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            return HttpResponseRedirect('/enter')
        h = get_restore_hash()
        try:
            r = Restore.objects.get(user__email=email)
            r.code = h
            r.save()
        except ObjectDoesNotExist:
            Restore.objects.create(user=user, code=h)
        send_email('Reset password',
                   email,
                   'Restore your password using this link:\nhttp://{}/reset_password?code={}'
                   .format(request.META['HTTP_HOST'], h))
        return HttpResponseRedirect('/enter')


def enter(request):
    if check_login(request.user):
        return HttpResponseRedirect('/main')
    if request.method == 'POST':
        user = authenticate(username=request.POST['email'].strip(), password=request.POST['password'])
        if user is not None:
            login(request, user)
        return HttpResponseRedirect('/enter')
    else:
        return render(request, "enter.html", context={"form": LoginForm()})
