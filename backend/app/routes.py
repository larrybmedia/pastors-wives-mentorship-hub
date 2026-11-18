import os
import secrets
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import desc
from . import db
from .models import User, Devotional, Course, Lesson, Event, MentorshipRequest, PrayerRequest, Post, Article

api=Blueprint("api",__name__)
def current_user():
    uid=get_jwt_identity()
    return db.session.get(User,int(uid)) if uid else None
def admin_required():
    u=current_user()
    return (u is not None and u.role=="admin" and u.status=="approved")
def err(msg,code=400): return jsonify(error=msg),code

@api.post("/auth/register")
def register():
    d=request.get_json() or {}; name=(d.get("name") or "").strip(); email=(d.get("email") or "").strip().lower(); pw=d.get("password") or ""
    if not name or not email or len(pw)<8: return err("Enter your name, a valid email and a password of at least 8 characters.")
    if User.query.filter_by(email=email).first(): return err("An account with this email already exists.",409)
    u=User(name=name,email=email,status="pending"); u.set_password(pw); db.session.add(u); db.session.commit()
    return jsonify(message="Registration received. Your account will be available after administrator approval."),201

@api.post("/auth/login")
def login():
    d=request.get_json() or {}; u=User.query.filter_by(email=(d.get("email") or "").lower().strip()).first()
    if not u or not u.check_password(d.get("password") or ""): return err("Invalid email or password.",401)
    if u.status!="approved": return err("Your membership is awaiting administrator approval." if u.status=="pending" else "This account is not active.",403)
    return jsonify(access_token=create_access_token(identity=str(u.id)),user=u.public())

@api.get("/auth/me")
@jwt_required()
def me():
    u=current_user()
    if not u or u.status!="approved": return err("Account is not active.",403)
    return jsonify(user=u.public())


@api.get("/public")
def public_content():
    today = datetime.now(
        ZoneInfo("Africa/Lagos")
    ).date().isoformat()

    devotional = Devotional.query.filter_by(
        date=today,
        published=True
    ).first()

    return jsonify(
        devotional=devotional.data() if devotional else None,
        courses=[
            c.data()
            for c in Course.query.filter_by(published=True).all()
        ],
        events=[
            e.data()
            for e in Event.query.filter_by(
                published=True
            ).order_by(Event.starts_at).all()
        ],
        articles=[
            a.data()
            for a in Article.query.filter_by(
                published=True
            ).order_by(Article.id.desc()).all()
        ],
        posts=[
            p.data()
            for p in Post.query.order_by(
                Post.id.desc()
            ).limit(30).all()
        ]
    )


@api.get("/devotionals/today")
def get_today_devotional():
    today = datetime.now(
        ZoneInfo("Africa/Lagos")
    ).date().isoformat()

    devotional = Devotional.query.filter_by(
        date=today,
        published=True
    ).first()

    if not devotional:
        return jsonify(
            devotional=None,
            message="Today's devotional is being prepared."
        ), 200

    return jsonify(devotional=devotional.data())


@api.get("/devotionals")
def get_devotionals():
    devotionals = (
        Devotional.query
        .filter_by(published=True)
        .order_by(Devotional.date.desc())
        .limit(30)
        .all()
    )

    return jsonify(
        devotionals=[d.data() for d in devotionals]
    )


@api.get("/community")
@jwt_required()
def community():
    return jsonify(posts=[p.data() for p in Post.query.order_by(Post.id.desc()).limit(50).all()])
@api.post("/community")
@jwt_required()
def create_post():
    u=current_user(); body=(request.json or {}).get("body","").strip()
    if not body or len(body)>5000: return err("Post must contain 1–5000 characters.")
    p=Post(user_id=u.id,body=body); db.session.add(p); db.session.commit()
    return jsonify(post=p.data()),201

@api.post("/mentorship")
@jwt_required()
def mentorship():
    d=request.json or {}; area=(d.get("area") or "").strip()
    if not area: return err("Please select an area of mentorship.")
    m=MentorshipRequest(user_id=current_user().id,area=area,goals=(d.get("goals") or "")[:4000]); db.session.add(m); db.session.commit()
    return jsonify(message="Your mentorship request has been submitted."),201

@api.post("/prayer")
@jwt_required()
def prayer():
    d=request.json or {}; msg=(d.get("message") or "").strip()
    if not msg: return err("Please enter your prayer request.")
    visibility=d.get("visibility","private")
    if visibility not in ["private","public"]: visibility="private"
    p=PrayerRequest(user_id=current_user().id,message=msg,visibility=visibility,anonymous=bool(d.get("anonymous")))
    db.session.add(p); db.session.commit()
    return jsonify(message="Your prayer request has been received."),201

@api.get("/admin/overview")
@jwt_required()
def overview():
    if not admin_required(): return err("Administrator access required.",403)
    return jsonify(pending_members=User.query.filter_by(status="pending").count(),
      members=User.query.filter_by(status="approved").count(),
      mentorship_requests=MentorshipRequest.query.filter_by(status="pending").count(),
      prayer_requests=PrayerRequest.query.count(), posts=Post.query.count())

@api.get("/admin/members")
@jwt_required()
def members():
    if not admin_required(): return err("Administrator access required.",403)
    return jsonify(members=[u.public() for u in User.query.order_by(User.created_at.desc()).all()])

@api.patch("/admin/members/<int:user_id>")
@jwt_required()
def member_status(user_id):
    if not admin_required(): return err("Administrator access required.",403)
    d=request.json or {}; status=d.get("status")
    if status not in ["approved","rejected","suspended"]: return err("Invalid membership status.")
    u=db.session.get(User,user_id)
    if not u: return err("Member not found.",404)
    u.status=status; db.session.commit()
    return jsonify(user=u.public())

@api.post("/admin/devotionals")
@jwt_required()
def add_devotional():
    if not admin_required(): return err("Administrator access required.",403)
    d=request.json or {}
    required=["date","verse","reference"]
    if any(not d.get(k) for k in required): return err("Date, verse and reference are required.")
    x=Devotional(date=d["date"],verse=d["verse"],reference=d["reference"],reflection=d.get("reflection",""),prayer=d.get("prayer",""),action=d.get("action",""),published=bool(d.get("published",True)))
    db.session.add(x); db.session.commit(); return jsonify(devotional=x.data()),201

@api.post("/admin/courses")
@jwt_required()
def add_course():
    if not admin_required(): return err("Administrator access required.",403)
    d=request.json or {}; title=(d.get("title") or "").strip()
    if not title: return err("Course title is required.")
    c=Course(title=title,description=d.get("description",""),published=bool(d.get("published",True))); db.session.add(c); db.session.flush()
    for i,item in enumerate(d.get("lessons",[]),1):
        db.session.add(Lesson(course_id=c.id,title=item.get("title","Lesson"),body=item.get("body",""),week_number=i))
    db.session.commit(); return jsonify(course=c.data()),201

@api.post("/admin/events")
@jwt_required()
def add_event():
    if not admin_required(): return err("Administrator access required.",403)
    d=request.json or {}
    if not d.get("title") or not d.get("starts_at"): return err("Title and start date/time are required.")
    e=Event(title=d["title"],description=d.get("description",""),starts_at=d["starts_at"],meeting_url=d.get("meeting_url",""),published=True)
    db.session.add(e); db.session.commit(); return jsonify(event=e.data()),201

@api.post("/admin/articles")
@jwt_required()
def add_article():
    if not admin_required(): return err("Administrator access required.",403)
    d=request.json or {}
    if not d.get("title"): return err("Article title is required.")
    a=Article(title=d["title"],category=d.get("category","Lifestyle"),excerpt=d.get("excerpt",""),body=d.get("body",""),published=True)
    db.session.add(a); db.session.commit(); return jsonify(article=a.data()),201



@api.post("/automation/devotional/prepare")
def prepare_devotional_automation():
    expected_secret = os.getenv("DEVOTIONAL_CRON_SECRET")
    supplied_secret = request.headers.get("X-Cron-Secret", "")

    if not expected_secret:
        return jsonify(error="Automation secret is not configured."), 503

    if not secrets.compare_digest(supplied_secret, expected_secret):
        return jsonify(error="Unauthorized."), 401

    try:
        from .devotional_service import prepare_tomorrow

        devotional = prepare_tomorrow()

        return jsonify(
            message="Tomorrow's devotional is prepared.",
            devotional=devotional.data()
        ), 200

    except Exception:
        db.session.rollback()
        logging.exception("Devotional preparation failed.")
        return jsonify(error="Devotional preparation failed."), 500


