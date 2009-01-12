import wsgiref.handlers


from google.appengine.ext import webapp

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
		template_values = {
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
			'locationurl': locationurl
		}
		viewhelpers.render_template(self, "views/location", template_values)


class ProfileHandler(webapp.RequestHandler):
	def get(self, current_url, profileurl):
		useraccount = models.get_current_auth_user(self)
		profile = models.UserAccount.get_by_key_name(profileurl)
		if not profile: 
			profile = False
		template_values = {
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
			'profile': profile,
			'profileurl': profileurl
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
			'itemurl': itemurl
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
		viewhelpers.render_template(self, "elements/postitem", template_values)

