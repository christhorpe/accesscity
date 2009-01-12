import os

from google.appengine.ext.webapp import template

# functions relating to platforms and user agents

def check_platform():
	if os.environ['HTTP_USER_AGENT'].find("iPhone") > -1:
		useragent_path = "platform/iphone"
	else:
		useragent_path = "platform/web"
	return useragent_path

# templates and template rendering

def get_template_url(endpoint):
	useragent_path = check_platform()
	template_url = "templates/" + useragent_path +"/"+ endpoint + ".html" 
	return template_url


def render_template(self, endpoint, templatevalues):
	path = os.path.join(os.path.dirname(__file__), get_template_url(endpoint))
	self.response.out.write(template.render(path, templatevalues))

