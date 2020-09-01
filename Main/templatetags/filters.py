from django import template
from Main.models import Solution, Task


register = template.Library()


@register.filter('mark_for_task')
def mark_for_task(task, user):
    try:
        return list(Solution.objects.filter(task=task, user=user, mark__isnull=False))[-1].mark
    except IndexError:
        return None


@register.filter('mark_for_block')
def mark_for_block(block, user):
    tasks = Task.objects.filter(block=block)
    if len(tasks) == 0:
        return None
    mark = 0
    flag = False
    for task in tasks:
        mft = mark_for_task(task, user)
        if mft:
            flag = True
            mark += mft * task.weight
    if flag:
        return round(mark)
    return None


@register.filter('marked')
def marked(mark):
    return bool(mark)


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
