from django import template
from Main.models import Solution, Task


register = template.Library()


@register.filter('mark_for_task')
def mark_for_task(task, user):
    try:
        return int(list(Solution.objects.filter(task=task, user=user, mark__isnull=False))[-1].mark * 10 / task.max_mark)
    except IndexError:
        return -1


@register.filter('mark_for_block')
def mark_for_block(block, user):
    tasks = Task.objects.filter(block=block)
    if len(tasks) == 0:
        return -1
    mark = 0
    flag = False
    for task in tasks:
        mft = mark_for_task(task, user)
        if mft >= 0:
            flag = True
            mark += mft * task.weight
    if flag:
        return round(mark)
    return -1


@register.filter('marked')
def marked(mark):
    print(mark)
    return mark != -1


@register.filter('mark_color')
def mark_color(mark):
    mark = round(mark)
    if mark > 7:
        return '#00FF00'
    elif mark > 5:
        return '#FFFF00'
    elif mark > 3:
        return '#FAD7A0'
    elif mark > 0:
        return '#F1948A'
    else:
        return '#FFFFFF'


@register.filter('in_dict')
def in_dict(value, dict):
    return value in dict.keys()
