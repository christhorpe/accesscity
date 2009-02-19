from google.appengine.api import users

import facebook
import oembed

def get_user_action_url(useraccount, current_url):
	if useraccount:
		user_action_url = users.create_logout_url("/")
	else:
		user_action_url = users.create_login_url(current_url)
	return user_action_url


def get_facebookapi():
	return facebook.Facebook("2be4a21659bf9ca4aac0c03423711af3", "99f269a008695061d570041bc756eecb")


def get_media_types():
	return ["Text", "Video", "Image"]
	
def get_form_tags():
	return ["Tip", "Fault", "Update"]

	
def get_oembed_links(text):
    consumer = oembed.OEmbedConsumer()
    # TODO add more oembed services and handle errors when none found
    flickr_endpoint = oembed.OEmbedEndpoint('http://www.flickr.com/services/oembed', 
                                    ['http://*.flickr.com/*'])
    youtube_endpoint = oembed.OEmbedEndpoint('http://oohembed.com/oohembed/',
                                    ['http://*.youtube.com/*'])
    consumer.addEndpoint(youtube_endpoint)
    consumer.addEndpoint(flickr_endpoint)
    response = consumer.embed(text)
    if response['html']:
        result =  response['html']
    else:
        result = response['url']
    return result
