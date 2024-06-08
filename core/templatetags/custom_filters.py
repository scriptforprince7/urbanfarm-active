# templatetags/custom_filters.py
from django import template
import re

register = template.Library()

@register.filter
def clean_title(value):
    # Use a regex to remove the variant part (e.g., "- (50Pcs)")
    return re.sub(r'\s*-\s*\(.*?\)$', '', value)
