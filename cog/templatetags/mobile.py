from django import template
import user_agents
from django.contrib.sites.models import Site
from cog.models import Project, Post
from django.shortcuts import get_object_or_404


register = template.Library()


@register.filter(name='detect_mobile')
def detect_mobile(ua_string):
    # ua_string = 'BlackBerry9700/5.0.0.862 Profile/MIDP-2.1 Configuration/CLDC-1.1 VendorID/331 UNTRUSTED/1.0 3gpp-gba'
    user_agent = user_agents.parse(ua_string)
    return user_agent.is_mobile
    # return True

@register.assignment_tag(name='get_project_list')
def get_project_list():
    project_list = Project.objects.filter(site=Site.objects.get_current()).order_by('short_name')
    return project_list


@register.filter(name='get_page_list')
def get_page_list(project_short_name):
    project = get_object_or_404(Project, short_name__iexact=project_short_name)
    page_list = Post.objects.filter(project=project).distinct().order_by('title')
    return page_list

