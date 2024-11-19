from app import app, db, load_user
from app.models import *
from app.forms import *
from flask import render_template, redirect, url_for, request
from flask_login import login_required, login_user, logout_user, current_user
import uuid
import datetime, time
import bcrypt
from app import cache

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index(): 
    return render_template('index.html')

@app.route('/users/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        if form.passwd.data == form.passwd_confirm.data:
            # using bcrypt, we create the "salted" hashed password.
            hash_password = bcrypt.hashpw(form.passwd.data.encode('utf-8'), bcrypt.gensalt())
            new_user = User()
            new_user.id = form.id.data
            new_user.description = form.description.data
            new_user.representative_name = form.representative_name.data
            new_user.email = form.email.data
            new_user.password = hash_password
            new_user.user_type = UserType.user

            db.session.add(new_user)
            db.session.commit()

            return render_template('index.html')
    return render_template('signup.html', form=form)

@app.route('/users/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=form.id.data).first()
        if user and bcrypt.checkpw(form.passwd.data.encode('utf-8'), user.password):
            login_user(user)
            getCache()
            return render_template('catalog.html', offers=cache.get("catalog"))
    return render_template('login.html', form=form)

@app.route('/users/signout', methods=['GET', 'POST'])
def signout():
    logout_user()
    return redirect(url_for('index'))

@login_required
@app.route('/catalog/<int:sort_by>', methods=['GET', 'POST'])
def catalog(sort_by):
    # 0 = desc
    # 1 = year
    # 2 = type
    # 3 = brand
    match sort_by:
        case 0:
            return render_template('catalog.html', offers=Offer.query.filter_by(status='opened').order_by(Offer.description.asc()).all())
        case 1:
            return render_template('catalog.html', offers=Offer.query.filter_by(status='opened').order_by(Offer.year.desc()).all())
        case 2:
            return render_template('catalog.html', offers=Offer.query.filter_by(status='opened').order_by(Offer.productType.asc()).all())
        case 3:
            return render_template('catalog.html', offers=Offer.query.filter_by(status='opened').order_by(Offer.brand.asc()).all())
    return render_template('catalog.html', offers=Offer.query.filter_by(status='opened').all())

@login_required
@app.route('/offers/create', methods=['GET', 'POST'])
def create_offer():
    form = CreateOffer()
    # print(form.validate_on_submit)
    if form.validate_on_submit():
        new_offer = Offer()
        new_offer.code = str(uuid.uuid4())
        new_offer.description = form.description.data
        new_offer.year = form.year.data
        new_offer.productType = form.productType.data
        new_offer.brand = form.brand.data.title()
        new_offer.price = form.price.data
        new_offer.status = 'opened'
        new_offer.seller_id = current_user.id

        db.session.add(new_offer) # adds offer to catalog
        current_user.offers.append(new_offer) # should add offer to current_user's offers list
        db.session.commit()

        catalog = getCache()
        return render_template('catalog.html', offers=catalog)
    return render_template('createoffer.html', form=form)

@login_required
@app.route('/offers/edit', methods=['GET', 'POST'])
def edit_offer():
    return render_template('editoffer.html', offers=current_user.offers)

@login_required
@app.route('/offers/edit/<string:code>', methods=['GET', 'POST'])
def edit_offer_request(code):
    form = CreateOffer()
    if form.validate_on_submit():
        offer = Offer.query.filter_by(code=code).one()
        offer.description = form.description.data
        offer.year = form.year.data
        offer.productType = form.productType.data
        offer.brand = form.brand.data
        offer.price = form.price.data

        db.session.add(offer)
        db.session.commit()

        catalog = getCache()
        return render_template('catalog.html', offers=catalog)
    
    return render_template('editofferrequest.html', offer=Offer.query.filter_by(code=code).one(), form=form)

@app.route('/director')
def director():
    return render_template('director.html')


@app.route('/offers/<string:code>/delete', methods=['GET','POST'])
@login_required
def delete_offer(code):
    offer = db.session.query(Offer).filter_by(code=code).one()
    db.session.delete(offer)
    db.session.commit()
    return render_template('editoffer.html', offers=current_user.offers)

@app.route('/offers/confirmation/<string:code>', methods=['GET', 'POST'])
@login_required
def confirmation(code):
    offer = Offer.query.filter_by(code = code).one()
    if offer in current_user.offers:
        return render_template('error.html')
    offer.status = 'accepted' # updates order status after 'Accept Offer' button from catalog is clicked
    offer.buyer_id = current_user.id
    db.session.add(offer)
    current_user.offers.append(offer) # adds the offer to the buyer's offers list
    db.session.commit()

    return render_template('confirmation.html', offer=offer)

@app.route('/catalog', methods=['GET', 'POST'])
@login_required
def refresh_catalog():
    catalog = getCache()
    return render_template('catalog.html', offers=catalog)

@app.route('/offers/update', methods=['GET','POST'])
@login_required
def update_status():
    offer_code = request.args.get('offer_code')
    offer = Offer.query.filter_by(code=offer_code).one()
    if offer.buyer_id == current_user.id:
        offer.status = 'received'
    else:
        offer.status = 'shipped'
    db.session.add(offer)
    db.session.commit()

    return render_template('editoffer.html', offers=current_user.offers)

def getCache():
    catalog = cache.get("catalog")
    if not catalog: 
        # cache miss!
        print('cache miss')
        catalog = Offer.query.filter_by(status='opened').all()
        cache.set("catalog", catalog)
    else:
        print('cache hit!')
    return catalog

@app.route('/users/<string:current_profile>', methods=['GET', 'POST'])
def profile(current_profile):
    form = CommentForm()
    u = User.query.filter_by(id = current_profile).one_or_none()
    if current_user:
        print("a user is logged in")
        if u:
            if current_user.id == u.id:
                print("this is the current user's profile")

    avg = 11
    if u is not None and len(u.reviews) > 0:
        avg = 0
        for review in u.reviews:
            avg += review.star_rating
        avg /= len(u.reviews)
        avg = round(avg, 2)

    # TODO THIS NEEDS TO RETURN ALL THE OBJECTS SORTED.
    # reviews sorted by date, replies sorted by date.
    # sorted_reviews = u.reviews.order_by(review.date)
    # u.reviews = sorted_reviews

    # for review in u.reviews:
    #     r = Review.query.filter_by(id=review.id).one_or_none()
    #     sorted_replies = sorted(r.reply, key=lambda x: x.date)
    #     r.reply = sorted_replies

    print(User.query.filter_by(id = current_profile).one_or_none() is not None)
    if form.validate_on_submit() and current_user and current_user != u.id:
        print("==================> " + str(form.stars.data))
        new_comment = Review(
            user_id = u.id,
            id = str(uuid.uuid4()),
            date = time.time(),
            star_rating = form.stars.data,
            comment = form.comment.data,
        )
        db.session.add(new_comment)
        db.session.commit()
        return render_template('profile.html', current_profile=u, avg=avg, form=form)

    if avg:
        return render_template('profile.html', current_profile=u, avg=avg, form=form)
    return render_template('profile.html', current_profile=u)

@app.route('/users/<string:current_profile>/<string:comment_id>', methods=['GET', 'POST'])
@login_required
def profile_reply(current_profile, comment_id):
    r = Review.query.filter_by(id=comment_id).one_or_none()
    sorted_replies = sorted(r.reply, key=lambda x: x.date)
    r.reply = sorted_replies
    for i in range(len(sorted_replies)):
        print(str(sorted_replies[i].date) + " --> " + str(sorted_replies[i].comment))
    reply_form = ReplyForm()
    print("form is : " + str(reply_form.validate_on_submit()))
    if reply_form.validate_on_submit():
        new_reply = Reply(
            review_id = comment_id,
            id = str(uuid.uuid4()),
            date = time.time(),
            comment = reply_form.comment.data
        )
        db.session.add(new_reply)
        db.session.commit()
        return profile(current_profile)
    return render_template('reply.html', form=reply_form, review=r)