from django import template

register = template.Library()

@register.filter
def split_lines(text):
    if text:
        return text.split('\n')
    return []