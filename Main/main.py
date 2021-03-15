from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError
from django.utils import timezone
from Main.models import *
from contextlib import contextmanager
from django.db.transaction import atomic
from random import choice
from string import ascii_letters
import smtplib
from threading import Thread
from time import sleep
from os import listdir, mkdir
from os.path import isdir, basename
from shutil import copyfile, rmtree
from copydetect import CopyDetector
import copydetect
from json import dumps


base_dir = 'data'


@contextmanager
def lock(key):
    pk = ThreadSafe.objects.get_or_create(key=key)[0].pk
    try:
        objs = ThreadSafe.objects.filter(pk=pk).select_for_update()
        with atomic():
            list(objs)
            yield None
    finally:
        pass


def get_in_html_tag(full, tag_name):
    try:
        return full.split('<div class="{}">'.format(tag_name))[1].split('</div>')[0]
    except IndexError:
        return ''


def random_string():
    letters = ascii_letters
    return ''.join(choice(letters) for _ in range(20))


def get_restore_hash():
    available = [r.code for r in Restore.objects.all()]
    while True:
        s = random_string()
        if s not in available:
            break
    return s


def send(subject, to_addr, body_text):
    from_addr = System.objects.get(key='email_address').value
    body = "\r\n".join((
        "From: %s" % from_addr,
        "To: %s" % to_addr,
        "Subject: %s" % subject,
        "",
        body_text
    ))

    server = smtplib.SMTP('SMTP.Office365.com', 587)
    server.starttls()
    server.login(System.objects.get(key='email_address').value, System.objects.get(key='email_password').value)
    server.sendmail(from_addr, [to_addr], body)
    server.quit()


def send_email(subject, to_addr, body_text):
    Thread(target=lambda: send(subject, to_addr, body_text)).start()


def check_login(user):
    return user.is_authenticated


def check_admin(user):
    if check_teacher(user):
        return True
    if not check_login(user):
        return False
    return len(Subscribe.objects.filter(user=user, is_assistant=True)) > 0


def check_teacher(user):
    return user.is_staff and check_login(user)


def check_god(user):
    return user.is_superuser and check_login(user)


def courses_available(user):
    if user.is_superuser:
        return Course.objects.all()
    else:
        return [s.course for s in Subscribe.objects.filter(user=user)]


def blocks_available(user):
    courses = courses_available(user)
    blocks = {}
    is_admin = check_admin(user)
    for course in courses:
        if is_admin:
            blocks[course] = Block.objects.filter(
                course=course
            )
        else:
            blocks[course] = Block.objects.filter(
                opened=True,
                time_start__lte=timezone.now(),
                course=course
            )
    return blocks


def can_send_solution(user, task):
    if user.is_superuser:
        return True
    try:
        s = Subscribe.objects.get(course=task.block.course, user=user)
    except ObjectDoesNotExist:
        return False
    if s.is_assistant:
        return True
    return task.block.time_start <= timezone.now() <= task.block.time_end and task.max_solutions_count > len(Solution.objects.filter(user=user, task=task)) and task.block.opened


def check_permission_block(user, block):
    blocks = blocks_available(user)
    for course in blocks.keys():
        if block in blocks[course]:
            return True
    return False


def is_integer(x):
    try:
        int(x)
        return True
    except ValueError:
        return False


def check_admin_on_course(user, course):
    if user.is_superuser:
        return True
    try:
        s = Subscribe.objects.get(user=user, course=course)
    except ObjectDoesNotExist:
        return False
    return s.is_assistant or user.is_staff


def comparer(value1, value2):
    if value1 < value2:
        return 1
    elif value1 == value2:
        return 0
    else:
        return -1


def result_comparer(result1, result2):
    verdicts = ['IN QUEUE', 'TESTING', 'TEST ERROR', 'SOLUTION ERROR', 'Compilation error', 'Time limit']
    if result1 in verdicts and result2 in verdicts:
        return comparer(verdicts.index(result1), verdicts.index(result2))
    if result1 in verdicts and result2 not in verdicts:
        return 1
    if result1 not in verdicts and result2 in verdicts:
        return -1
    return comparer(int(result1.split('/')[0]), int(result2.split('/')[0]))


def solutions_filter(request):
    try:
        solutions = list(reversed(Solution.objects.filter(task__block_id=request['block_id'])))
    except MultiValueDictKeyError as e:
        return [Solution.objects.get(id=request['id'])]
    if 'solution_id' in request.keys():
        solutions = [solution for solution in solutions if any([solution.id == int(i) for i in request['solution_id'].strip().split()])]
    if 'task_name' in request.keys():
        solutions = [solution for solution in solutions if solution.task.name == request['task_name']]
    if 'user' in request.keys():
        solutions = [solution for solution in solutions if str(solution.userinfo) == request['user']]
    if 'group' in request.keys():
        solutions = [solution for solution in solutions if solution.userinfo.group == request['group']]
    if 'best_result' in request.keys():
        sols = {}
        for solution in solutions:
            if (solution.user.username, solution.task.id) in sols.keys():
                comp = result_comparer(sols[(solution.user.username, solution.task.id)][0].result, solution.result)
                if comp == 1:
                    sols[(solution.user.username, solution.task.id)] = [solution]
                elif comp == 0:
                    sols[(solution.user.username, solution.task.id)].append(solution)
            else:
                sols[(solution.user.username, solution.task.id)] = [solution]
        solutions = []
        for sol in sols.values():
            for val in sol:
                solutions.append(val)
        solutions = list(sorted(solutions, key=lambda s: s.id, reverse=True))
    if 'last_solution' in request.keys():
        visited = []
        new_solutions = []
        for solution in solutions:
            if (solution.user.username, solution.task.id) not in visited:
                visited.append((solution.user.username, solution.task.id))
                new_solutions.append(solution)
        solutions = new_solutions
    if 'only_students' in request.keys():
        solutions = [solution for solution in solutions if not check_admin_on_course(solution.user, solution.task.block.course)]
    if 'not_seen' in request.keys():
        solutions = [solution for solution in solutions if solution.mark == None]
    return sorted(solutions, key=lambda s: s.id, reverse=True)


def re_test(solutions_request, request):
    from .Tester import Tester
    for sol in solutions_request:
        sol.details = ''
        with open(sol.log_file, 'wb') as fs:
            fs.write(b'')
        sol.save()
        Thread(target=lambda: Tester(sol, request.META['HTTP_HOST']).push()).start()
        sleep(.1)


def block_solutions_info(block):
    all_solutions = Solution.objects.filter(task__block=block)
    all_users = [solution.userinfo for solution in all_solutions]
    return {
        'tasks': sorted(list(set([solution.task for solution in all_solutions])), key=lambda x: x.name),
        'users': sorted(list(set(all_users)), key=lambda x: str(x)),
        'groups': sorted(list(set([userinfo.group for userinfo in all_users])), key=lambda x: str(x))
    }


def delete_folder(path):
    flag = True
    while flag:
        try:
            rmtree(dirname(cur_folder))
            flag = False
        except:
            pass


def solution_path(path):
    files = [x for x in listdir(path) if x.endswith('.sln') and not x.startswith('.')]
    if files:
        return path
    return ''.join([solution_path(join(path, file)) for file in listdir(path) if isdir(join(path, file))])


def register_user(u):
    password = random_string()
    user = User.objects.create_user(username=u['email'], email=u['email'], password=password)
    UserInfo.objects.create(
        surname=u['surname'],
        name=u['name'],
        middle_name=u['middle_name'],
        group=u['group'],
        user=user
    )
    send_email('You have been registered in Sprint!', u['email'],
                'Your password is: {}\nPlease change it after login in settings!\nhttps://sprint.cshse.ru/'.format(password))


def check_cheating(solutions, block, cheating_percent):
    block.cheating_checking = True
    block.save()
    try:
        cheating_data = {}
        cheating_path = join(MEDIA_ROOT, 'cheating', str(block.id))
        if exists(cheating_path):
            rmtree(cheating_path)
        mkdir(cheating_path)
        for solution in solutions:
            for file in solution.user_files.keys():
                user_file = join(MEDIA_ROOT, 'solutions', str(solution.id), file)
                dest_file = join(cheating_path, '_'.join([str(solution.id), basename(file)]))
                copyfile(user_file, dest_file)
        files_len = len(solutions)
        files = listdir(cheating_path)
        for i in range(len(files) - 1):
            for j in range(i + 1, len(files)):
                file1 = files[i]
                file2 = files[j]
                s1 = file1.split('_')
                s2 = file2.split('_')
                sol1 = Solution.objects.get(id=int(s1[0]))
                sol2 = Solution.objects.get(id=int(s2[0]))
                filename1 = '_'.join(s1[1:])
                filename2 = '_'.join(s2[1:])
                if sol1.user == sol2.user or sol1.task != sol2.task or filename1 != filename2:
                    continue
                fp1 = copydetect.CodeFingerprint(join(cheating_path, file1), 25, 1)
                fp2 = copydetect.CodeFingerprint(join(cheating_path, file2), 25, 1)
                token_overlap, similarities, slices = copydetect.compare_files(fp1, fp2)
                similarity = (similarities[0] + similarities[1]) / 2
                if similarity >= cheating_percent / 100:
                    if sol1.user.id not in cheating_data.keys():
                        cheating_data[sol1.user.id] = []
                    if sol2.user.id not in cheating_data.keys():
                        cheating_data[sol2.user.id] = []
                    cheating_data[sol1.user.id].append({
                        'source': True,
                        'solution': sol1.id,
                        'file': filename1,
                        'similar': sol2.id,
                        'similarity': round(similarity * 100, 2)
                    })
                    cheating_data[sol2.user.id].append({
                        'source': False,
                        'solution': sol2.id,
                        'file': filename2,
                        'similar': sol1.id,
                        'similarity': round(similarity * 100, 2)
                    })
    finally:
        if exists(cheating_path):
            rmtree(cheating_path)
        with open(block.cheating_results_path, 'w') as fs:
            fs.write(dumps(cheating_data))
        block = Block.objects.get(id=block.id)
        block.cheating_checking = False
        block.save()
        print('finished')
    
