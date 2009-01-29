import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.db import djangoforms
from google.appengine.ext import db

import models
import helpers
import viewhelpers
import facebook

class MainHandler(webapp.RequestHandler):
	def get(self, current_url):
		useraccount = models.get_current_auth_user(self)
		items = models.get_latest_text_items(10)
		template_values = {
			'ratingform': models.RatingForm(),
			'itemform': models.ItemForm(),
			'media_types': helpers.get_media_types(),
			'form_tags': helpers.get_form_tags(),
			'locations': models.Location.all().order('name'),
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
			'items': items,
		}
		viewhelpers.render_template(self, "views/home", template_values)


class LocationHandler(webapp.RequestHandler):
	def get(self, current_url, locationurl):
		useraccount = models.get_current_auth_user(self)
		location = models.Location.gql("WHERE indexname = :1", locationurl.lower()).get()
		items = models.get_items_for_location(location, 20, 0)
		locationrating = models.LocationRatings.gql("WHERE location = :1", location).get()
		userlocations = models.get_userlocations_for_location(location, 10, 0)
		template_values = {
			'items': items,
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
			'locationurl': locationurl,
			'ratingform': models.RatingForm(),
			'itemform': models.ItemForm(),
			'media_types': helpers.get_media_types(),
			'form_tags': helpers.get_form_tags(),
			'locations': models.Location.all().order('name'),
			'locationrating': locationrating,
			'userlocations': userlocations,
		}
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
	def post(self, current_url, itemurl):
		useraccount = models.get_current_auth_user(self)
		tag = self.request.get("tag")
		media_type = self.request.get("media_type")
		form = models.ItemForm(data=self.request.POST)
		location = models.Location.get(self.request.get("location"))
		created = False
		item = False
		if form.is_valid():
			item = form.save(commit=False)
			item.useraccount = useraccount
			item.location = location
			item.tag = tag
			item.media_type = media_type
			item.put()
			created = True
			models.kill_location_items_cache(location)
			userlocation = models.log_userlocation_activity(location, useraccount, False)
		template_values = {
			'created':created,
			'itemform':form,
			'media_types': helpers.get_media_types(),
			'form_tags': helpers.get_form_tags(),
			'locations': models.Location.all().order('name'),
			'location': location,
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
			'ajax_item': self.request.get("item_ajax_submit")
		}
		if item:
			template_values['item'] = item
		if self.request.get("item_ajax_submit"):
			viewhelpers.render_template(self, "views/ajaxitem", template_values)
		else:
			viewhelpers.render_template(self, "views/item", template_values)


class ItemLocationHandler(webapp.RequestHandler):
	def get(self, current_url, locationurl):
		location = models.Location.gql("WHERE indexname = :1", locationurl.lower()).get()
		items = models.get_items_for_location(location, 20, 0)
		template_values = {
							"items": items,
		}
		viewhelpers.render_template(self, "ajaxviews/locationitems", template_values)


class ContentHandler(webapp.RequestHandler):
	def get(self, current_url):
		useraccount = models.get_current_auth_user(self)
		template_values = {
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
			'current_url': current_url
		}
		viewhelpers.render_template(self, "content/"+ current_url, template_values)


	

class RatingHandler(webapp.RequestHandler):
    def post(self, current_url, id):
        useraccount = models.get_current_auth_user(self)
        
        location_key = self.request.get('id_location_key')
        location = models.Location.get(location_key)
        
        template_values = {
			'useraccount': useraccount,
			'location' : location
		}
        ratingform = models.RatingForm(self.request.POST)
        
        if ratingform.is_valid():
            rating = ratingform.save(commit=False)
            
            rating.location = location
            rating.useraccount = useraccount
            rating.put()
            
            # create LocationRatings
            locationrating = None
            locationrating = models.LocationRatings.gql("WHERE location = :1", location).get()
                        
            if not locationrating:
                locationrating = models.LocationRatings()
                locationrating.location = location
            
            if rating.when == "peak":
                locationrating.peak_count += 1
                locationrating.peak_busy_sum += rating.busyness
                locationrating.peak_easy_sum += rating.howeasy
                locationrating.peak_step_sum += rating.steps
            if rating.when == "offpeak":
                locationrating.offpeak_count += 1
                locationrating.offpeak_busy_sum += rating.busyness
                locationrating.offpeak_easy_sum += rating.howeasy
                locationrating.offpeak_step_sum += rating.steps
            if rating.when == "weekend":
                locationrating.weekend_count += 1
                locationrating.weekend_busy_sum += rating.busyness
                locationrating.weekend_easy_sum += rating.howeasy
                locationrating.weekend_step_sum += rating.steps
            
            locationrating.put()
            #locationrating.{rating.when}_count = 
            template_values['message'] = "Rating Created"
        else:
            template_values["error_message"] = "Error occurrred creating rating"
            template_values["ratingform"] = ratingform
        
        viewhelpers.render_template(self, "views/created", template_values)
    
