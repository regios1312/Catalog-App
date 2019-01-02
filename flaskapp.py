from flask import Flask, render_template, jsonify, request
from flask import url_for, redirect, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from permission import Base, Category, Items, User
from sqlalchemy import desc
from flask import session as login_session
import random
import string

from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

engine = create_engine('sqlite:///newcatalog.db')

Base.metadata.bind = engine

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']

APPLICATION_NAME = 'Item Catalog App'


# A function to create a session object
def session_create():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session


# The homepage of catalog project.Does not provide
# CRUD functionality if not logged in.
@app.route('/')
@app.route('/catalog')
def categorydisplay():
    session = session_create()
    mycategory = session.query(Category).all()
    mylatestitems = session.query(Items).order_by(desc(Items.itemid)).all()
    if 'username' not in login_session:
        return render_template('notloggedinhome.html',
                               mycategory=mycategory,
                               mylatestitems=mylatestitems)
    else:
        return render_template('home.html',
                               mycategory=mycategory,
                               mylatestitems=mylatestitems)


# display the interested item once you click on it.
# Also provides link to edit and delete if logged in.
@app.route('/catalog/categories/<string:category_name>/<string:item_name>/')
def displayitem(category_name, item_name):
    session = session_create()
    mycategory = session.query(Category).filter_by(name=category_name).first()
    myitem = session.query(Items).filter_by(name=item_name).first()
    if 'username' not in login_session:
        return render_template('publicshowitem.html',
                               myitem=myitem,
                               mycategory=mycategory)
    else:
        return render_template('showitem.html',
                               myitem=myitem,
                               mycategory=mycategory)


# Displays all the items belonging to a particular category
@app.route('/catalog/categories/<string:category_name>/')
def listitems(category_name):
    session = session_create()
    desiredcategory = session.query(Category).filter_by(
                      name=category_name).first()
    categoryitems = session.query(Items).filter_by(
                    category_id=desiredcategory.cid).all()
    allcategories = session.query(Category).all()
    return render_template('listitem.html',
                           categoryitems=categoryitems,
                           desiredcategory=desiredcategory,
                           allcategories=allcategories)


# Adds an item to the database
@app.route('/catalog/categories/additem', methods=['GET', 'POST'])
def AddItem():
    session = session_create()
    mycategory = session.query(Category).all()
    items = session.query(Items).all()
    if request.method == 'POST':
        formid = session.query(Category).filter_by(
                 name=request.form['category']).first()
        additem = Items(name=request.form['name'],
                        itemid=len(items)+1,
                        price=request.form['price'],
                        description=request.form['description'],
                        user_id=login_session['user_id'],
                        category_id=formid.cid)
        session.add(additem)
        session.commit()
        return redirect(url_for('categorydisplay'))
    return render_template('additem.html', mycategory=mycategory)


# Deletes the item from database
@app.route('/catalog/categories/<string:category_name>/'
           + '<string:item_name>/delete', methods=['GET', 'POST'])
def DeleteItem(category_name, item_name):
    session = session_create()
    mycategory = session.query(Category).filter_by(name=category_name).first()
    myitem = session.query(Items).filter_by(name=item_name).first()
    if ('username' not in login_session or
       myitem.user_id != getUserID(login_session['email'])):
        return render_template('noauthorization.html',
                               mycategory=mycategory,
                               myitem=myitem)
    if request.method == 'POST':
        session.delete(myitem)
        flash('Item %s successfully deleted' % myitem.name)
        session.commit()
        return redirect(url_for('categorydisplay',
                                mycategory=mycategory,
                                myitem=myitem))
    return render_template('deleteitem.html', mycategory=mycategory,
                           myitem=myitem)


# edits/updates an existing item
@app.route('/catalog/categories/<string:category_name>/'
           + '<string:item_name>/edit', methods=['GET', 'POST'])
def EditItem(category_name, item_name):
    session = session_create()
    categoryall = session.query(Category).all()
    mycategory = session.query(Category).filter_by(name=category_name).first()
    myitem = session.query(Items).filter_by(name=item_name).first()
    updateitem = session.query(Items).filter_by(name=item_name).first()
    if ('username' not in login_session or
       updateitem.user_id != getUserID(login_session['email'])):
        return render_template('noauthorization.html',
                               mycategory=mycategory,
                               myitem=myitem)
    if request.method == 'POST':
        if request.form['name']:
            updateitem.name = request.form['name']
        if request.form['price']:
            updateitem.price = request.form['price']
        if request.form['description']:
            updateitem.description = request.form['description']
        if request.form['category']:
            formid = session.query(Category).filter_by(
                     name=request.form['category']).first()
            updateitem.category_id = formid.cid
        session.add(updateitem)
        session.commit()
        return redirect(url_for('categorydisplay'))
    return render_template('edititem.html',
                           mycategory=mycategory,
                           myitem=myitem, categoryall=categoryall)


# provides a json endpoint to view contents of database if logged in.
@app.route('/catalog.json')
def endpoint():
        session = session_create()
        categories = session.query(Category).all()
        return jsonify(category=[i.serialize for i in categories])


@app.route('/catalog/categories/<string:category_name>'
           + '/<string:item_name>/json')
def itemjson(category_name, item_name):
    session = session_create()
    item = session.query(Items).filter_by(name=item_name).first()
    return jsonify(item=[item.serialize])


# Creates a user in case the user is not in the database.
def createUser(login_session):
    session = session_create()
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(
           email=login_session['email']).first()
    return user.id


# A function which returns the interested user object
def getUserInfo(user_id):
    session = session_create()
    user = session.query(User).filter_by(id=user_id).first()
    return user


# A function which returns the id of user if he exists
def getUserID(email):
    session = session_create()
    try:
        user = session.query(User).filter_by(email=email).first()
        return user.id
    except:
        return None


# provides a status code while logging in
@app.route('/login')
def showlogin():
    state = ''.join(random.choice(string.ascii_uppercase+string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# the google OAuth signin function for checking authorization of the user
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already'
                                            + ' connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;" '
    output += ' "border-radius: 150px;" '
    output += ' "-webkit-border-radius: 150px;" '
    output += ' "-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# A function to disconnect from current login session.
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not'
                                            + 'connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
           % login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        return redirect(url_for('categorydisplay'))
    else:
        response = make_response(json.dumps('Failed to'
                                 + ' revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# The main function to run the server
if __name__ == '__main__':
    app.debug = True
    app.secret_key = "super_secret_key"
    app.run(host='0.0.0.0', port=5000)
