import random

from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.ext.webapp import template
from google.appengine.ext.db import djangoforms
from google.appengine.api import users
from google.appengine.ext import webapp

import helpers
import facebook


class UserAccount(db.Model):
	# Meta data which decorates externally held authentication details (i.e. GMail, Facebook, OpenID) and which holds information such as 
	user = db.UserProperty()
	fbid = db.IntegerProperty()
	network = db.StringProperty()
	profiletext = db.TextProperty()
	profileid = db.StringProperty()
	name = db.StringProperty()
	tempdetails = db.BooleanProperty(default=True)
	thumbnail = db.StringProperty()
	phone = db.StringProperty()
	created_at = db.DateTimeProperty(auto_now_add=True)
	updated_at = db.DateTimeProperty()
	itemcount = db.IntegerProperty(default=0)
	ratingcount = db.IntegerProperty(default=0)
	actioncount = db.IntegerProperty(default=0)


class DataSource(db.Model):
	# where to store information about where the data has come from
	name = db.StringProperty()
	version = db.StringProperty()
	location = db.StringProperty()
	contact = db.TextProperty()


class APIKey(db.Model):
	# storing API keys for each app
	keystring = db.StringProperty()
	name = db.StringProperty()
	developer = db.TextProperty()
	created_at = db.DateTimeProperty(auto_now_add=True)
	updated_at = db.DateTimeProperty(auto_now=True)	


class Location(search.SearchableModel):
	name = db.StringProperty()
	address = db.TextProperty()
	location_type = db.StringProperty()
	datasource = db.ReferenceProperty(DataSource)
	datasource_fkid = db.StringProperty()
	shortname = db.StringProperty()
	indexname = db.StringProperty()
	lat = db.StringProperty()
	lng = db.StringProperty()
	created_at = db.DateTimeProperty(auto_now_add=True)
	updated_at = db.DateTimeProperty(auto_now=True)	
	itemcount = db.IntegerProperty(default=0)
	ratingcount = db.IntegerProperty(default=0)
	photo_url = db.StringProperty()
	photo_credit = db.StringProperty()


class LocationRatings(db.Model):
	location = db.ReferenceProperty(Location)
	offpeak_count = db.IntegerProperty(default=0)
	peak_count = db.IntegerProperty(default=0)
	weekend_count = db.IntegerProperty(default=0)
	offpeak_easy_sum = db.IntegerProperty(default=0)
	offpeak_step_sum = db.IntegerProperty(default=0)
	offpeak_busy_sum = db.IntegerProperty(default=0)
	peak_easy_sum = db.IntegerProperty(default=0)
	peak_step_sum = db.IntegerProperty(default=0)
	peak_busy_sum = db.IntegerProperty(default=0)
	weekend_easy_sum = db.IntegerProperty(default=0)
	weekend_step_sum = db.IntegerProperty(default=0)
	weekend_busy_sum = db.IntegerProperty(default=0)




class UserLocation(db.Model):
	location = db.ReferenceProperty(Location)
	useraccount = db.ReferenceProperty(UserAccount)
	follow = db.BooleanProperty(default=False)
	interaction = db.StringProperty()
	created_at = db.DateTimeProperty(auto_now_add=True)
	updated_at = db.DateTimeProperty(auto_now=True)	


def get_userlocations_for_location(location, limit, page):
	query = db.Query(UserLocation)
	query.filter("location = ", location)
	query.filter("follow = ", False)
	query.order("-updated_at")
	userlocations = query.fetch(limit, 0)
	return userlocations


def get_userlocations_for_user(useraccount):
	userlocations = UserLocation.all().filter("useraccount = ", useraccount).order("-updated_at")
	return userlocations

def get_userlocation_activity(location, useraccount, follow):
	userlocation = False
	userlocation = db.Query(UserLocation).filter("location =", location).filter("useraccount =", useraccount).filter("follow =", follow).get()
	return userlocation

	
def log_userlocation_activity(location, useraccount, follow):
	userlocation = get_userlocation_activity(location, useraccount, follow)
	if not userlocation:
		userlocation = UserLocation()
		userlocation.location = location
		userlocation.useraccount = useraccount
		userlocation.follow = False
		userlocation.interaction = "item"
		userlocation.put()
	return userlocation
	
	
	

class Item(db.Model):
	location = db.ReferenceProperty(Location)
	useraccount = db.ReferenceProperty(UserAccount)
	source = db.ReferenceProperty(APIKey)
	media_type = db.StringProperty()
	tag = db.StringProperty()
	title = db.StringProperty(required=True)
	url = db.StringProperty()
	text = db.TextProperty(required=True)
	created_at = db.DateTimeProperty(auto_now_add=True)
	updated_at = db.DateTimeProperty(auto_now=True)	


def get_latest_text_items(limit):
	items = None
	query = db.Query(Item)
	query.filter("media_type = ", "Text")
	query.order("-created_at")
	items = query.fetch(limit, 0)
	return items

def get_items_for_location(location, limit, page):
	items = None
	query = db.Query(Item)
	query.filter("location = ", location)
	query.order("-created_at")
	items = query.fetch(limit, 0)
	return items

def get_featured_items(type, limit):
	items = None
	query = db.Query(Item)
	query.filter("media_type = ",type)
	query.order("-created_at")
	items = query.fetch(limit, 0)
	return items


class ItemForm(djangoforms.ModelForm):
  class Meta:
    model = Item
    exclude = ['created', 'updated', 'tag', 'source', 'url', 'useraccount', 'location', 'media_type']


	
class Rating(db.Model):
	location = db.ReferenceProperty(Location)
	useraccount = db.ReferenceProperty(UserAccount)
	when = db.StringProperty(default="Peak",required=True,choices=['peak', 'offpeak', 'weekend'])
	how_easy = db.IntegerProperty(default=3, required=True,choices=[1,2,3,4,5])
	steps = db.IntegerProperty(default=3, required=True,choices=[1,2,3,4,5])
	busyness = db.IntegerProperty(default=3, required=True,choices=[1,2,3,4,5])
	created_at = db.DateTimeProperty(auto_now_add=True)
	updated_at = db.DateTimeProperty(auto_now=True)	


class RatingForm(djangoforms.ModelForm):
    class Meta:
        model = Rating
        exclude = ['useraccount', 'location', 'created_at', 'updated_at']
    

# elements for sharded counter
	
class CounterConfig(db.Model):
	name = db.StringProperty(required=True)
	num_shards = db.IntegerProperty(required=True, default=1)

class Counter(db.Model):
	name = db.StringProperty(required=True)
	count = db.IntegerProperty(required=True, default=0)



# START methods from Google relating to sharded counters


def get_counter(name):
	total = 0
	for counter in Counter.gql('WHERE name = :1', name):
		total += counter.count
	return total


def increment_counter(name):
	config = CounterConfig.get_or_insert(name, name=name)
	def txn():
		index = random.randint(0, config.num_shards - 1)
		shard_name = name + str(index)
		counter = Counter.get_by_key_name(shard_name)
		if counter is None:
			counter = Counter(key_name=shard_name, name=name)
		counter.count += 1
		counter.put()
	db.run_in_transaction(txn)

# END methods from Google relating to sharded counters

# sequence methods for creating id's

def get_new_gmailid():
	increment_counter("gmail_sequence")
	return str(get_counter("gmail_sequence")).zfill(10)


def get_new_locationid():
	increment_counter("location_sequence")
	return str(get_counter("location_sequence")).zfill(10)


def get_new_itemid():
	increment_counter("item_sequence")
	return str(get_counter("item_sequence")).zfill(16)



# method to look up user account

def get_user_account(user, fbid):
	useraccount = False
	query = db.Query(UserAccount)
	if user:
		query.filter('user =', user)
	else:
		query.filter('fbid =', fbid)
	useraccount = query.get()
	return useraccount


# methods to create useraccount objects 

def create_user_account_from_gmail(user):
	profileid = "gm" + get_new_gmailid()
	useraccount = UserAccount(key_name=profileid)
	useraccount.profileid = profileid
	useraccount.network = "gmail"
	useraccount.user = user
	useraccount.name = user.nickname()
	if useraccount.name.find("@") > 0:
		temp = useraccount.name.split("@")
		useraccount.name = temp[0]
	useraccount.put()
	increment_counter("total_users")
	increment_counter("gmail_users")
	return useraccount


def create_user_account_from_facebook(user):
	profileid = "fb" + str(user['uid'])
	useraccount = UserAccount(key_name=profileid)
	useraccount.profileid = profileid
	useraccount.network = "facebook"
	useraccount.fbid = user['uid']
	useraccount.name = user['name']
	useraccount.put()
	increment_counter("total_users")
	increment_counter("facebook_users")
	return useraccount


# get currently logged in user

def get_current_auth_user(self):
	nickname = ""	
	useraccount = False
	gmailuser = users.get_current_user()
	facebookapi = helpers.get_facebookapi()
	if facebookapi.check_session(self.request):
		fbuser = facebookapi.users.getInfo([facebookapi.uid], ['uid', 'name'])[0]
		useraccount = get_user_account("", fbuser['uid'])
		if not useraccount:
			useraccount = create_user_account_from_facebook(fbuser)
	if gmailuser:
		useraccount = get_user_account(gmailuser, "")
		if not useraccount:
			useraccount = create_user_account_from_gmail(gmailuser)
	return useraccount



# methods relating to content for a user

def get_user_items(useraccount):
	items = Item.all().filter("useraccount =", useraccount).order("-created_at")
	return items

def get_user_ratings(useraccount):
	ratings = Rating.all().filter("useraccount =", useraccount).order("-created_at")
	return ratings

