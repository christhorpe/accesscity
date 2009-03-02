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
		items = models.get_latest_text_items(5)
		video_featured_items = models.get_featured_items("Video",1)
		image_featured_items = models.get_featured_items("Image", 3)
		
		usercount = models.get_counter("total_users")
		itemcount = models.get_counter("total_items")
		ratingcount = models.get_counter("total_ratings")
		locationcount = models.get_counter("total_locations")
		template_values = {
			'ratingform': models.RatingForm(),
			'itemform': models.ItemForm(),
			'media_types': helpers.get_media_types(),
			'form_tags': helpers.get_form_tags(),
			'locations': models.Location.all().order('name'),
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
			'items': items,
			'usercount': usercount,
			'itemcount': itemcount,
			'ratingcount': ratingcount,
			'locationcount': locationcount,
			'image_featured_items': image_featured_items
		}
		if video_featured_items:
		    template_values['video_featured_items'] = video_featured_items[0]
		
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
			'location': location,
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
		userlocations = False
		useraccount = models.get_current_auth_user(self)
		profile = models.UserAccount.get_by_key_name(profileurl)
		if profile:
			items = models.get_user_items(profile)
			ratings = models.get_user_ratings(profile)
			userlocations = models.get_userlocations_for_user(profile)
		template_values = {
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
			'profile': profile,
			'items': items,
			'ratings': ratings,
			'userlocations': userlocations,
		}
		viewhelpers.render_template(self, "views/profile", template_values)


class ItemHandler(webapp.RequestHandler):
	def get(self, current_url, itemurl):
		useraccount = models.get_current_auth_user(self)
		template_values = {
			'useraccount': useraccount,
			'user_action_url': helpers.get_user_action_url(useraccount, current_url),
			'itemurl': itemurl,
			'locations': models.Location.all().order('name'),
			'itemform': models.ItemForm(),
			'ratingform': models.RatingForm(),
			'media_types': helpers.get_media_types(),
			'form_tags': helpers.get_form_tags()
		}
		item = models.Item.get(itemurl)
		if item:
		    template_values['location'] = item.location
		    template_values['locationrating'] = models.LocationRatings.gql("WHERE location = :1", item.location).get()
		    template_values['item'] = item
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
			# Handle oembed
			if (item.media_type == "Video") or (item.media_type == "Image"):
			    item.url = helpers.get_oembed_links(item.text)
			    models.kill_featured_caches()
			item.put()
			location.itemcount += 1
			location.put()
			useraccount.itemcount +=1
			useraccount.actioncount +=1
			useraccount.put()
			created = True
			models.kill_location_items_cache(location)
			userlocation = models.log_userlocation_activity(location, useraccount, False)
			models.increment_counter("total_items")
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
			'location' : location,
			'ajax_rating': self.request.get("rating_ajax_submit")
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
                locationrating.peak_easy_sum += rating.how_easy
                locationrating.peak_step_sum += rating.steps
            if rating.when == "offpeak":
                locationrating.offpeak_count += 1
                locationrating.offpeak_busy_sum += rating.busyness
                locationrating.offpeak_easy_sum += rating.how_easy
                locationrating.offpeak_step_sum += rating.steps
            if rating.when == "weekend":
                locationrating.weekend_count += 1
                locationrating.weekend_busy_sum += rating.busyness
                locationrating.weekend_easy_sum += rating.how_easy
                locationrating.weekend_step_sum += rating.steps
            
            locationrating.put()
            models.increment_counter("total_ratings")
            models.kill_location_items_cache(location)
            template_values['ratingform'] = models.RatingForm()
            template_values['message'] = "Rating Created"
            template_values['locationrating'] = locationrating
            template_values['created'] = True
        else:
            template_values["error_message"] = "Error occurrred creating rating"
            template_values["ratingform"] = ratingform
            template_values["created"] = False
        
        if locationrating:
        	template_values['locationrating'] = locationrating
        
        if self.request.get("rating_ajax_submit"):
        	viewhelpers.render_template(self, "elements/ratingform", template_values)
        else:
            viewhelpers.render_template(self, "views/created", template_values)
    
