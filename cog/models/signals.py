'''
Module containing methods for processing signals generated by model objects lifecycle.
'''

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from cog.plugins.esgf.security import esgfDatabaseManager
from cog.models import UserProfile, ProjectTag, getProjectForGroup
from cog.models.user_profile import createUsername
from cog.utils import getJson
from cog.views.utils import get_all_shared_user_info
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

import logging

log = logging.getLogger()

# callback receiver function for UserProfile post_save events
@receiver(post_save, sender=UserProfile, dispatch_uid="user_profile_post_save")
def account_created_receiver(sender, **kwargs):

    # retrieve arguments
    userp = kwargs['instance']
    created = kwargs['created']

    #print 'Signal received: UserProfile post_save: username=%s created=%s openids=%s' % (userp.user.username, created, userp.openids())

    # if username is like "openiduserXXX", then change it to the last part of the openid (+XXX if necessary)
    if created and userp.openid() is not None: # only for new accounts created with external openid
        if userp.user.username.startswith("openiduser"): # typically from "https://ceda.ac.uk/openid/..." 
            # change the username
            lastPartOfOpenid = userp.openid().split("/")[-1]
            username = createUsername(lastPartOfOpenid)
            log.debug("New user: changing the username from: %s to: %s" % (userp.user.username, username))
            userp.user.username = username
            userp.user.save()

def update_user_projects_at_login(sender, user, request, **kwargs):
    '''Updates the user projects every time the user logs in.'''
    
    update_user_projects(user)
        
def update_user_projects(user):
    '''
    Function to update the user projects from across the federation.
    Will query all remote nodes
    (but NOT the current nodes, since that information should already be up-to-date)
    and save the updated information in the local database.
    '''

    if user.is_authenticated():
        
        # current user groups in local database
        ugroups = user.groups.all()
         
        # retrieve map of (project, groups) for this user
        (projTuples, grpTuples) = get_all_shared_user_info(user, includeCurrentSite=False)
        
        # add new memberships for remote projects
        remoteGroups = [] # updated list of remote groups
        for (project, roles) in projTuples:
            log.debug(
                'Updating membership for user: %s project: %s roles: %s' % (
                    user.profile.openid(), project.short_name, roles
                )
            )
            
            for role in roles:
                group = project.getGroup(role)
                remoteGroups.append(group)
                if not group in ugroups:
                    log.debug('Adding group: %s to user: %s' % (group, user))
                    user.groups.add(group)
                   
        # persist changes to local database 
        user.save()
                    
        # remove old memberships for remote projects
        for group in user.groups.all():
            try:
                project = getProjectForGroup(group)
                # do not change local projects
                if not project.isLocal():
                    if not group in remoteGroups:
                        log.debug('Removing group: %s from user: %s' % (group, user))
                        user.groups.remove( group )
            except ObjectDoesNotExist:
                log.warning('Cannot retrieve project for group=%s, removing obsolete group' % group)
                user.groups.remove( group )
            
        # persist changes to local database
        user.save()
                                                   
def update_user_tags(user):
    '''Function to update the user tags from their home node.'''
    
    if user.profile.openid() is not None:
        
        openid = user.profile.openid()
        url = "http://%s/share/user/?openid=%s" % (user.profile.site.domain, user.profile.openid())
        log.debug('Updating user tags: querying URL=%s' % url)
        jobj = getJson(url)
        
        if jobj is not None and openid in jobj['users'] and 'project_tags' in jobj['users'][openid]:
            
            # loop over tags found on user home node
            tags = []
            for tagName in jobj['users'][openid]['project_tags']:
                try:
                    tags.append( ProjectTag.objects.get(name__iexact=tagName) )
                except ObjectDoesNotExist:
                    pass # tag not found in local database
            
            # store tags in local user profile
            userProfile = UserProfile.objects.get(id=user.profile.id)
            userProfile.tags.clear()
            userProfile.tags = tags
            userProfile.save()
            transaction.commit()
            log.debug('User: %s updated for tags: %s' % (user, tags))
    
# NOTE: connecting the login signal is not needed because every time the user logs in,
# the session is refreshed and updating of projects is triggered already by the CoG session middleware
#user_logged_in.connect(update_user_projects_at_login)