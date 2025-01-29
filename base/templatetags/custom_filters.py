from django import template

register = template.Library()

@register.filter
def split_and_format(value):
    """
    Split a string by semicolons and format text before colons as bold.
    """
    if not value:
        return []
    
    # Handle both strings and lists
    if isinstance(value, list):
        items = value
    else:
        items = value.split(";")

    formatted_items = []
    
    for item in items:
        if ":" in item:
            bold_part, normal_part = item.split(":", 1)
            formatted_items.append((bold_part.strip() + ":", normal_part.strip()))
        else:
            formatted_items.append((None, item.strip()))
    
    return formatted_items
