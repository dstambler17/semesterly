from social import *
from student.models import *
import urllib2, json, pprint, datetime
from django.conf import settings
from django.db import models
import json, requests, httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


DAY_LIST = ['M','T','W','R','F','S','U'];

def next_weekday(d, weekday):
    d = d - datetime.timedelta(days=1)
    days_ahead = DAY_LIST.index(weekday) - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

def create_student(strategy, details, response, user, *args, **kwargs):
    backend_name = kwargs['backend'].name
    if Student.objects.filter(user=user).exists():
    	new_student = Student.objects.get(user=user)
    else:
        new_student = Student(user=user)
        new_student.save()
    social_user = user.social_auth.filter(
        provider=backend_name,
    ).first()

    if backend_name == 'google-oauth2':
      try:
        access_token = social_user.extra_data["access_token"]
      except TypeError:
        access_token = json.loads(social_user.extra_data)["access_token"]
      response = requests.get(
          'https://www.googleapis.com/plus/v1/people/me'.format(
            social_user.uid,
            settings.GOOGLE_API_KEY),
          params={'access_token': access_token}
      )
      new_student.img_url = response.json()['image']['url']
      new_student.gender = response.json()['gender']
      new_student.save()

    elif backend_name == 'facebook':

      try:
        access_token = social_user.extra_data["access_token"]
      except TypeError:
        access_token = json.loads(social_user.extra_data)["access_token"]

      if social_user:
          url = u'https://graph.facebook.com/{0}/' \
                u'?fields=picture&type=large' \
                u'&access_token={1}'.format(
                    social_user.uid,
                    access_token,
                )
          request = urllib2.Request(url)
          data = json.loads(urllib2.urlopen(request).read())
          new_student.img_url = data['picture']['data']['url']
          url = u'https://graph.facebook.com/{0}/' \
                u'?fields=gender' \
                u'&access_token={1}'.format(
                    social_user.uid,
                    access_token,
                )
          request = urllib2.Request(url)
          data = json.loads(urllib2.urlopen(request).read())
          try:
            new_student.gender = data.get('gender','')
          except:
            pass
          new_student.fbook_uid = social_user.uid
          new_student.save()
          url = u'https://graph.facebook.com/{0}/' \
                u'friends?fields=id' \
                u'&access_token={1}'.format(
                    social_user.uid,
                    access_token,
                )
          request = urllib2.Request(url)
          friends = json.loads(urllib2.urlopen(request).read()).get('data')
          
          for friend in friends:
            if Student.objects.filter(fbook_uid=friend['id']).exists():
              friend_student = Student.objects.get(fbook_uid=friend['id'])
              if not new_student.friends.filter(user=friend_student.user).exists():
                new_student.friends.add(friend_student)
                new_student.save()
                friend_student.save()

    return kwargs
    