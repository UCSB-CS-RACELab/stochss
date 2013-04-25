import jinja2
import os
import cgi
import datetime
import urllib
import webapp2
import logging

from webapp2_extras import sessions
from webapp2_extras import sessions_memcache
from webapp2_extras import auth

from google.appengine.ext import db
from google.appengine.api import users

""" Initializer section """

# Initialize the jinja environment
jinja_environment = jinja2.Environment(autoescape=True,
                                       loader=(jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))) 


class BaseHandler(webapp2.RequestHandler):
    """
    The base handler that extends the dispatch() method to start the session store and save all sessions at the end of a request:
    It also has helper methods for storing and retrieving objects from session and for rendering the response to the clients.
    All the request handlers should extend this class.
    """
    def __init__(self, request, response):
        self.user = users.get_current_user()
        webapp2.RequestHandler.__init__(self, request, response)
        
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)
        # Using memcache for storing sessions.
        self.session = self.session_store.get_session(name='mc_session', factory=sessions_memcache.MemcacheSessionFactory)
        
        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)
    
    def get_session_property(self, key):
        """ Get the value for the given session property. """
        
        try:
            return self.session[key]            
        except KeyError:
            return None
    
    def set_session_property(self, key, value):
        """ Set the value for the given session property. """
        
        self.session[key] = value
            
    def render_response(self, _template, **context):
        """ Process the template and render response. """
        ctx = {'user': self.user}
        ctx.update(context)
        if 'model_edited' not in ctx:
            model_edited = self.get_session_property('model_edited')
            if model_edited is not None:
                ctx.update({'model_edited': model_edited.name})
            
        template = jinja_environment.get_template(_template)
        self.response.out.write(template.render({'active_upload': True}, **ctx))

class Signout(BaseHandler):
    """ Signout handler that clears the current user's session and redirects to the signout url. """
    def get(self):
        # First, check if the recent changes have been saved.
        is_model_saved = self.get_session_property('is_model_saved')
        if is_model_saved is not None and not is_model_saved:
            logging.debug("Model not saved!")
            result = {'status': False, 'save_msg': 'Please save your changes first!', 'is_saved': False, 'redirect_page': '/signout'}
            self.render_response('modeleditor.html', **result)
            return
        
        self.session.clear()
        self.redirect(users.create_logout_url('/'))


class MainPage(BaseHandler):
    """ The Main page. Renders a welcome message and shortcuts to main menu items. """

    def get(self):
        self.render_response("mainpage.html")
    
    def post(self):
        self.get()


class VisualizePage(webapp2.RequestHandler):
    """ Render a page for visualization of simulation resutls. """
    def get(self):
        template = jinja_environment.get_template('visualizepage.html')
        self.response.out.write(template.render({'active_visualize': True}))
        

class StatusPage(webapp2.RequestHandler):
    """ Render a page for viewing job status. """
    def get(self):
        template = jinja_environment.get_template('statuspage.html')
        self.response.out.write(template.render({'active_visualize': True}))

class CredentialsPage(webapp2.RequestHandler):
    """ Render a page for viewing job status. """
    def get(self):
        template = jinja_environment.get_template('credentials.html')
        self.response.out.write(template.render({'active_visualize': True}))


config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'my-super-secret-key',
}

from handlers.specieseditor import *
from handlers.modeleditor import *
from handlers.parametereditor import *
from handlers.reactioneditor import *
from handlers.simulation import *
from handlers.credentials import *


app = webapp2.WSGIApplication([                                                              
                               ('/', MainPage),
                               ('/modeleditor/specieseditor', SpeciesEditorPage),
                               ('/modeleditor/reactioneditor', ReactionEditorPage),
                               ('/modeleditor/parametereditor', ParameterEditorPage),
                               ('/modeleditor/import/fromfile', ModelEditorImportFromFilePage),
                               ('/modeleditor/import/examplelibrary', ModelEditorImportFromLibrary),
                               ('/modeleditor/export/tostochkit2', ModelEditorExportToStochkit2),
                               ('/modeleditor.*', ModelEditorPage),
                               ('/simulate',SimulatePage),
                               ('/simulate/newstochkitensemble',NewStochkitEnsemblePage),
                               ('/simulate/jobsettings',JobSettingsPage),
                               ('/visualize',VisualizePage),
                               ('/status',StatusPage),
                               ('/credentials',CredentialsPage),
                               ('/signout', Signout)
                               ],
                                config = config,
                                debug=True) 


logging.getLogger().setLevel(logging.DEBUG)

if __name__ == '__main__':
    main()
