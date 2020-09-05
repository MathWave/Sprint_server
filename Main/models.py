from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_delete
from os.path import sep, join
from os import remove


base_dir = 'data'


class ThreadSafe(models.Model):
    key = models.CharField(max_length=80, unique=True)


class Course(models.Model):
    name = models.TextField()

    @property
    def teachers(self):
        return [UserInfo.objects.get(user=s.user) for s in Subscribe.objects.filter(user__is_staff=1, course=self)]

    @property
    def subscribes(self):
        return Subscribe.objects.filter(course=self)

    def __str__(self):
        return self.name


class Block(models.Model):
    name = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    time_start = models.DateTimeField()
    time_end = models.DateTimeField()
    opened = models.IntegerField()

    def __str__(self):
        return self.name

    @property
    def tasks(self):
        return Task.objects.filter(block=self)

    @property
    def time_start_chrome(self):
        return self.time_start.strftime("%Y-%m-%dT%H:%M")

    @property
    def time_end_chrome(self):
        return self.time_end.strftime("%Y-%m-%dT%H:%M")

    @property
    def is_opened(self):
        return 'checked' if self.opened else ''

    @property
    def solutions(self):
        return reversed(Solution.objects.filter(task__block=self))

    @property
    def subscribed_users(self):
        return [UserInfo.objects.get(user=s.user) for s in Subscribe.objects.filter(course=self.course)]


class Restore(models.Model):
    code = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class Subscribe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    is_assistant = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username + '|' + self.course.name

    @property
    def userinfo(self):
        return UserInfo.objects.get(user=self.user)

    @property
    def role(self):
        if self.user.is_superuser:
            return 'Администратор'
        if self.user.is_staff:
            return 'Преподаватель'
        return 'Ассистент' if bool(self.is_assistant) else 'Студент'


class Task(models.Model):
    name = models.TextField()
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    legend = models.TextField(default='')
    input = models.TextField(default='')
    output = models.TextField(default='')
    specifications = models.TextField(default='')
    time_limit = models.IntegerField(default=10000)
    weight = models.FloatField(default=1.0)
    max_mark = models.IntegerField(default=10)
    max_solutions_count = models.IntegerField(default=10)

    def __str__(self):
        return self.name

    def tests_path(self):
        return join(base_dir, 'tests', str(self.id) + '.cs')

    @property
    def tests_text(self):
        return open(self.tests_path(), 'r').read()

    @property
    def tests_uploaded(self):
        from os.path import exists
        return exists(self.tests_path())

    @property
    def files(self):
        return ExtraFile.objects.filter(task=self)


class UserInfo(models.Model):
    surname = models.TextField()
    name = models.TextField()
    middle_name = models.TextField()
    group = models.TextField()
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    new_block_notification = models.IntegerField(default=0)
    mark_notification = models.IntegerField(default=0)

    def __str__(self):
        return "{} {} {}".format(self.surname, self.name, self.middle_name)


class Solution(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    result = models.TextField()
    details = models.TextField(default='')
    time_sent = models.DateTimeField(null=True)
    mark = models.IntegerField(null=True)
    comment = models.TextField(default='')

    def __str__(self):
        return self.task.name + '|'+ self.user.username

    def path(self):
        return join(base_dir, 'solutions', str(self.id))

    @property
    def userinfo(self):
        return UserInfo.objects.get(user=self.user)

    @property
    def mark_property(self):
        return str(self.mark) if self.mark is not None else 'нет оценки'

    @property
    def mark_select(self):
        line = ''
        if self.mark:
            line += '<option value="нет оценки">нет оценки</option>'
        else:
            line += '<option value="нет оценки" selected>нет оценки</option>'
        for mark in range(self.task.max_mark + 1):
            if mark == self.mark:
                line += '<option value="{}" selected>{}</option>'.format(mark, mark)
            else:
                line += '<option value="{}">{}</option>'.format(mark, mark)
        return line

    @property
    def comment_property(self):
        return self.comment if self.comment else 'нет комментария'

    @staticmethod
    def get_files(path):
        from os import listdir
        from os.path import isfile, join
        files_dict = {}
        for file in listdir(path):
            if file.startswith('.') or file == '__MACOSX' or file == 'test_folder' or file == 'bin' or file == 'obj':
                continue
            current_file = join(path, file)
            if isfile(current_file):
                if not current_file.endswith('.csproj') and not current_file.endswith('.sln'):
                    try:
                        files_dict[sep.join(current_file.split(sep)[6:])] \
                            = open(current_file, 'rb').read().decode('UTF-8')
                    except UnicodeDecodeError:
                        pass
            else:
                files_dict = {**files_dict, **Solution.get_files(current_file)}
        return files_dict

    @property
    def files(self):
        return Solution.get_files(self.path())


class System(models.Model):
    key = models.TextField()
    value = models.TextField()

    def __str__(self):
        return self.key


class ExtraFile(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    file = models.FileField(upload_to=join(base_dir, 'extra_files'))
    filename = models.TextField()

    @property
    def readable(self):
        try:
            open(self.file.path, 'rb').read().decode('UTF-8')
            return True
        except UnicodeDecodeError:
            return False

    @property
    def text(self):
        return open(self.file.path, 'r').read()
    

    def __str__(self):
        return self.filename


@receiver(post_delete, sender=Task)
def delete_task_hook(sender, instance, using, **kwargs):
    from os.path import exists
    if exists(instance.tests_path()):
        from os import remove
        remove(instance.tests_path())


@receiver(post_delete, sender=Solution)
def delete_solution_hook(sender, instance, using, **kwargs):
    from os.path import exists
    if exists(instance.path()):
        from shutil import rmtree
        rmtree(instance.path())


@receiver(post_delete, sender=ExtraFile)
def delete_file_hook(sender, instance, using, **kwargs):
    remove(instance.file.path)
