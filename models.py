import random

from google.appengine.ext import db
from google.appengine.api import users

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
	updated_at = db.DateTimeProperty()	


class Location(db.Model):
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
	updated_at = db.DateTimeProperty()
	itemcount = db.IntegerProperty(default=0)
	ratingcount = db.IntegerProperty(default=0)


class UserLocations(db.Model):
	location = db.ReferenceProperty(Location)
	useraccount = db.ReferenceProperty(UserAccount)
	created_at = db.DateTimeProperty(auto_now_add=True)
	updated_at = db.DateTimeProperty()


class Item(db.Model):
	location = db.ReferenceProperty(Location)
	useraccount = db.ReferenceProperty(UserAccount)
	source = db.ReferenceProperty(APIKey)
	media_type = db.StringProperty()
	title = db.StringProperty()
	url = db.StringProperty()
	text = db.TextProperty()
	created_at = db.DateTimeProperty(auto_now_add=True)
	updated_at = db.DateTimeProperty()
	tag = db.StringProperty()
	embed_link = db.StringProperty()

	
class Rating(db.Model):
	location = db.ReferenceProperty(Location)
	useraccount = db.ReferenceProperty(UserAccount)
	busyness = db.IntegerProperty(default=3)
	facilities = db.IntegerProperty(default=3)
	accessibility = db.IntegerProperty(default=3)
	comment = db.TextProperty()
	created_at = db.DateTimeProperty(auto_now_add=True)
	updated_at = db.DateTimeProperty()


# elements for sharded counter
	
class CounterConfig(db.Model):
	name = db.StringProperty(required=True)
	num_shards = db.IntegerProperty(required=True, default=1)

class Counter(db.Model):
	name = db.StringProperty(required=True)
	count = db.IntegerProperty(required=True, default=0)



#methods 




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


def get_new_gmailid():
	increment_counter("gmail_sequence")
	return str(get_counter("gmail_sequence")).zfill(10)


def get_new_locationid():
	increment_counter("location_sequence")
	return str(get_counter("location_sequence")).zfill(10)


def get_new_itemid():
	increment_counter("item_sequence")
	return str(get_counter("item_sequence")).zfill(16)


def get_user_account(user, fbid):
	useraccount = False
	query = db.Query(UserAccount)
	if user:
		query.filter('user =', user)
	else:
		query.filter('fbid =', fbid)
	useraccount = query.get()
	return useraccount


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
	return useraccount


def create_user_account_from_facebook(user):
	profileid = "fb" + str(user['uid'])
	useraccount = UserAccount(key_name=profileid)
	useraccount.profileid = profileid
	useraccount.network = "facebook"
	useraccount.fbid = user['uid']
	useraccount.name = user['name']
	useraccount.put()
	return useraccount


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