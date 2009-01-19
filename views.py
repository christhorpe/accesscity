import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext import db

import models
import helpers
import viewhelpers
import facebook

class MainHandler(webapp.RequestHandler):
	def get(self, current_url):
		useraccount = models.get_current_auth_user(self)
		template_values = {
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url)
		}
		viewhelpers.render_template(self, "views/home", template_values)


class LocationHandler(webapp.RequestHandler):
	def get(self, current_url, locationurl):
		useraccount = models.get_current_auth_user(self)
		location_name = locationurl.replace("-"," ")
		template_values = {
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
			'locationurl': location_name
		}
		
		location = models.Location.gql("WHERE name = :1", location_name).get()
        
		if location:
		    template_values['location'] = location
		
		viewhelpers.render_template(self, "views/location", template_values)


class ProfileHandler(webapp.RequestHandler):
	def get(self, current_url, profileurl):
		# set all objects to be passed to template as False so we won't get object passed before instantiated errors
		profile = False
		items = False
		ratings = False
		locations = False
		useraccount = models.get_current_auth_user(self)
		profile = models.UserAccount.get_by_key_name(profileurl)
		if profile:
			items = models.get_user_items(profile)
			ratings = models.get_user_ratings(profile)
		template_values = {
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
			'profile': profile,
			'items': items,
			'ratings': ratings,
			'locations': locations,
		}
		viewhelpers.render_template(self, "views/profile", template_values)


class ItemHandler(webapp.RequestHandler):
	def get(self, current_url, itemurl):
		useraccount = models.get_current_auth_user(self)
		template_values = {
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
			'itemurl': itemurl
		}
		viewhelpers.render_template(self, "views/location", template_values)


class ContentHandler(webapp.RequestHandler):
	def get(self, current_url):
		useraccount = models.get_current_auth_user(self)
		template_values = {
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
			'current_url': current_url
		}
		viewhelpers.render_template(self, "content/"+ current_url, template_values)


class CreateItemHandler(webapp.RequestHandler):
	def get(self, current_url):
		useraccount = models.get_current_auth_user(self)
		template_values = {
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
		}
		viewhelpers.render_template(self, "elements/itemform", template_values)
	
	def post(self, current_url):
		useraccount = models.get_current_auth_user(self)
		template_values = {
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
		}
		errors = 0
		# validate parameters
		required_fields = ["title","text","media_type","tag", "source"]
		
		for field in required_fields:
		    if len(self.request.get(field)) == 0:
		        template_values["error_message"] = "Missing Fields"
		        errors = 1
                viewhelpers.render_template(self, "views/home", template_values)
		
		
		if errors == 0:
		    # handle parameters
		    item = models.Item()
		    item.title = self.request.get('title')
		    item.text = self.request.get('text')
		    item.media_type = self.request.get('media_type')
		    item.tag = self.request.get('tag')
		    template_values["message"] = "Item Created"
		    
		    item.put()
		    self.redirect('/')
	
	