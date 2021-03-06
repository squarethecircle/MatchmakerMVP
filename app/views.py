from flask import render_template,session,redirect,url_for,request,flash,jsonify
from app import app,models,facebook
from random import randint
from models import Match

blacklist = [1598222289,1389627032,100007479487216,100009034776491]

@facebook.tokengetter
def get_facebook_token(token=None):
    return session.get('facebook_token')


@app.route('/login')
def login():
	return facebook.authorize(callback = app.config['APP_DOMAIN']+'oauth_authorized')

@app.route('/oauth_authorized')
@facebook.authorized_handler
def oauth_authorized(resp):
	next_url = request.args.get('next') or url_for('index')
	if resp is None:
		flash(u'You denied the request to sign in.')
		return redirect(next_url)
	session['facebook_token'] = (resp['access_token'], resp['expires'])
	session['fbid'] = facebook.get('me?fields=id').data['id']
	return redirect('/index')

@app.route('/')
@app.route('/index')
def index():
	return "Hello World"
@app.route('/match',methods=['GET'])
def match():

	#resp = facebook.get('me/friends?fields=name,id,education')
	if session.get('friends') is None:
		session['friends'] = facebook.get('v1.0/fql?q=SELECT%20name%2Cuid%2Crelationship_status%2Csex%20FROM%20user%20WHERE%20uid%20IN%20(SELECT%20uid1%20FROM%20friend%20WHERE%20uid2%3Dme())%20and%20(%27Yale%20University%27%20in%20education%20or%20%27Yale%27%20in%20affiliations)').data['data']
	male_friends = []
	female_friends = []
	#return jsonify({'data':session['friends']})
	for friend in session['friends']:
		if friend['sex'] == 'male' and friend['relationship_status'] != 'In a relationship':
			if friend['uid'] not in blacklist:
				male_friends.append(friend)
		elif friend['sex'] == 'female' and friend['relationship_status'] != 'In a relationship':
			if friend['uid'] not in blacklist:
				female_friends.append(friend)
	session['male_friends'] = male_friends
	session['female_friends'] = female_friends
	match_pair = (male_friends[randint(0,len(male_friends)-1)],female_friends[randint(0,len(female_friends)-1)])

	return render_template('match.html',boy=match_pair[0]['name'], girl=match_pair[1]['name'],
			boypp=getPhoto(match_pair[0]['uid']),girlpp=getPhoto(match_pair[1]['uid']),
			boyid=match_pair[0]['uid'],girlid=match_pair[0]['uid'])

@app.route('/match',methods=['POST'])
def acceptMatch():
	friend1 = request.form.get('friend1')
	friend2 = request.form.get('friend2')
	friend1name = request.form.get('friend1name')
	friend2name = request.form.get('friend2name')
	if request.form.get('result') == 'accept':
		query = Match.objects(friends__all=[friend1,friend2]).first()
		if query == None:
			new_match = Match(friends=[friend1,friend2],friend_names=[friend1name,friend2name],matchers=[session['fbid']],num_matchers=1,nonmatchers=[],num_nonmatchers=0,confirmed=False).save()
		elif session['fbid'] not in query.matchers:
			query.matchers.append(session['fbid'])
			query.num_matchers += 1
			query.save()
	elif request.form.get('result') == 'reject':
		query = Match.objects(friends__all=[friend1,friend2]).first()
		if query == None:
			new_match = Match(friends=[friend1,friend2],friend_names=[friend1name,friend2name],matchers=[],num_matchers=0,nonmatchers=[session['fbid']],num_nonmatchers=1,confirmed=False).save()
		elif session['fbid'] not in query.nonmatchers:
			query.nonmatchers.append(session['fbid'])
			query.num_nonmatchers += 1
			query.save()
	match_pair = (session['male_friends'][randint(0,len(session['male_friends'])-1)],session['female_friends'][randint(0,len(session['female_friends'])-1)])
	new_match={'boy':match_pair[0]['name'],'girl':match_pair[1]['name'],'boypp':getPhoto(match_pair[0]['uid']),
				'girlpp':getPhoto(match_pair[1]['uid']),'boyid':match_pair[0]['uid'],
				'girlid':match_pair[0]['uid']}
	return jsonify(new_match)

def getPhoto(uid):
	photo = facebook.get('v1.0/fql?q=SELECT%20pic_crop%20from%20profile%20where%20id%3D'+str(uid)).data['data'][0]['pic_crop']
	return photo['uri']




