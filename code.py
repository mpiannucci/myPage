""" Basic blog using webpy 0.3 """
import web
import model
import random
from hashlib import sha1

### Map out the urls
urls = (
    '/', 'Index',
    '/blog', 'Blog',
    '/view/(\d+)', 'View',
    '/new', 'New',
    '/delete/(\d+)', 'Delete',
    '/edit/(\d+)', 'Edit',
    '/admin', 'Admin',
    '/projects', 'Projects',
    '/contact', 'Contact',
    '/logout', 'Logout',
    '/like/(\d+)', 'Like',
    '/dislike/(\d+)', 'Dislike',
    '/resume', 'Resume'
)

### Create a cryptography for the passwords
class PasswordHash(object):
    def __init__(self, password_):
        self.salt = "".join(chr(random.randint(33,127)) for x in xrange(64))
        self.saltedpw = sha1(password_ + self.salt).hexdigest()
    def check_password(self, password_):
        """checks if the password is correct"""
        return self.saltedpw == sha1(password_ + self.salt).hexdigest()

### Defines the username and password to access admin interface 
### TO DO --  STORE IN DATABASE INSTEAD 
users = {
    
}

names = model.get_users()
for name in names:
    users[name.username] = PasswordHash(name.password)

### Toggle the web debug (to test sessions)
#web.config.debug = False

### Define the web templates
t_globals = {
    'datestr': web.datestr
}
render = web.template.render('templates', base='base', globals=t_globals)

### Create the web app and the sessions
app = web.application(urls, globals())

### Create the session
if web.config.get('_session') is None:
    session = web.session.Session(app, web.session.DiskStore('sessions'),
                              initializer={'user': 'anonymous'})
    web.config._session = session
else:
    session = web.config._session

signin_form = web.form.Form(web.form.Textbox('username',
                                     web.form.Validator('Unknown username.',
                                                    lambda x: x in users.keys()),
                                     description='Username:'),
                        web.form.Password('password',
                                      description='Password:'),
                        validators = [web.form.Validator("Username and password didn't match.",
                                      lambda x: users[x.username].check_password(x.password)) ])

### Start the Web page class definitions
class Index:
    """ Show the home page """
    def GET(self):
        return render.index()

class Blog:
    """ Create the layout for the blog """
    def GET(self):
        """ Show all page """
        posts = model.get_posts()
        return render.blog(posts)

class View:
    """ Create a simgle post view for testing """
    def GET(self, id):
        """ View single post """
        post = model.get_post(int(id))
        return render.view(post)


class New:
    """ Create the new post form """
    form = web.form.Form(
        web.form.Textbox('title', web.form.notnull, 
            size=30,
            description="Post title:"),
        web.form.Textarea('content', web.form.notnull, 
            rows=30, cols=60,
            description="Post content:"),
        web.form.Button('Post entry'),
    )

    """ Create the page used to create new blog posts """
    def GET(self):
        form = self.form()
        return render.new(form)

    def POST(self):
        form = self.form()
        if not form.validates():
            return render.new(form)
        model.new_post(form.d.title, form.d.content)
        posts = model.get_posts()
        return render.admin(session.user, posts)

class Delete:
    """ Create the method to delete posts """
    def POST(self, id):
        model.del_post(int(id))
        posts = model.get_posts()
        return render.admin(session.user, posts)

class Edit:
    """ Create the method to edit posts """
    def GET(self, id):
        post = model.get_post(int(id))
        form = New.form()
        form.fill(post)
        return render.edit(post, form)


    def POST(self, id):
        form = New.form()
        post = model.get_post(int(id))
        if not form.validates():
            return render.edit(post, form)
        model.update_post(int(id), form.d.title, form.d.content)
        posts = model.get_posts()
        return render.admin(session.user, posts)

class Admin:
    """ Create the Admin interface """    
    def GET(self):
        if session.user != 'anonymous':
            posts = model.get_posts()
            return render.admin(session.user, posts)
        else:
            form = signin_form()
            return render.login(session.user, form)
    
    def POST(self):
        form = signin_form()
        if not form.validates(): 
            return render.login(session.user, form)
        else:
            session.user = form['username'].value
            posts = model.get_posts()
            return render.admin(session.user, posts) 

class Logout:
    """Create the log out method"""
    def GET(self):
        session.kill()
        raise web.seeother('/blog')

class Projects:
    """ Redirect to Github """
    def GET(self):
        raise web.seeother('https://github.com/rhodysurf')

class Resume:
    """ Serve the resume """
    def GET(self):
        raise web.seeother('/static/MatthewIannucciResume.pdf')

class Contact:
    """ Create a contact page """
    def GET(self): 
        return render.contact()

class Like:
    """ Create the method to like a post """
    def GET(self, id):
        post = model.get_post(int(id))
        like = post.likes
        model.like_post(int(id), int(like))
        raise web.seeother('/blog')

class Dislike:
    """ Create the method to dislike a post """
    def GET(self, id):
        post = model.get_post(int(id))
        dlike = post.dislikes
        model.dislike_post(int(id), int(dlike))
        raise web.seeother('/blog')

def notfound():
    """ Create the not found page """
    return web.notfound("Sorry, the page you were looking for was not found.")
    # You can use template result like below, either is ok:
    #return web.notfound(render.notfound())
    #return web.notfound(str(render.notfound()))

def internalerror():
    """ Create the internal error page """
    return web.internalerror("The server says: No soup for you!")

### Create the not found app
app.notfound = notfound
app.internalerror = internalerror

if __name__ == '__main__':
    app.run()
