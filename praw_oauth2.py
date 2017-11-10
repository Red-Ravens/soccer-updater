#!/usr/bin/env python3
#####################################
#    LAST UPDATED     10 NOV 2017   #
#####################################
"""Make PRAW OAuth2 less terrible"""
import praw


def redravens(usragent=None):
    """
    Log in to /u/RedRavens via OAuth2    
    :param usragent: Optional useragent    
    :return: praw.Reddit instance    
    """    
    client = 'ZKgKQILuoGYHHA'    
    key = 'blah'    
    refresh = 'blah'
    if usragent:
        useragent = usragent
    else:
        useragent = '/r/ussoccer RPI server v3.0 by RedRavens'    
     
     reddit = praw.Reddit(user_agent=useragent, client_id=client, client_secret=key,
                          refresh_token=refresh)
     return reddit
     
     
 def ussoccer_bot(usragent=None):
     """
     Log in to /u/ussoccer_bot via OAuth2
     :param usragent: Optional user agent    
     :return: praw.Reddit instance    
     """    
     client = 'SCfVt7C2ZVrPmg'    
     key = 'blah'    
     refresh = 'blah'    
     if usragent:        
         useragent = usragent
     else:        
         useragent = '/r/ussoccer RPI server v3.0 by RedRavens'    
      
     reddit = praw.Reddit(user_agent=useragent, client_id=client, client_secret=key,
                          refresh_token=refresh) 
     
     return reddit
