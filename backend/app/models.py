from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(120), nullable=False)
    email=db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash=db.Column(db.String(255), nullable=False)
    role=db.Column(db.String(30), default="member", nullable=False)
    status=db.Column(db.String(30), default="pending", nullable=False)
    bio=db.Column(db.Text, default="")
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
    def set_password(self,p): self.password_hash=generate_password_hash(p)
    def check_password(self,p): return check_password_hash(self.password_hash,p)
    def public(self): return {"id":self.id,"name":self.name,"email":self.email,"role":self.role,"status":self.status,"bio":self.bio}


class Devotional(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.String(10), unique=True, nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    theme = db.Column(db.String(200), default="")

    verse = db.Column(db.Text, nullable=False)
    reference = db.Column(db.String(100), nullable=False)

    reflection = db.Column(db.Text, default="")
    application = db.Column(db.Text, default="")
    prayer = db.Column(db.Text, default="")
    action = db.Column(db.Text, default="")

    published = db.Column(db.Boolean, default=False, nullable=False)
    generated_by = db.Column(db.String(30), default="manual")
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def data(self):
        return {
            "id": self.id,
            "date": self.date,
            "title": self.title,
            "theme": self.theme,
            "verse": self.verse,
            "reference": self.reference,
            "reflection": self.reflection,
            "application": self.application,
            "prayer": self.prayer,
            "action": self.action,
            "published": self.published
        }

class Course(db.Model):
    id=db.Column(db.Integer,primary_key=True); title=db.Column(db.String(180),nullable=False)
    description=db.Column(db.Text,default=""); published=db.Column(db.Boolean,default=False)
    lessons=db.relationship("Lesson",backref="course",cascade="all, delete-orphan")
    def data(self): return {"id":self.id,"title":self.title,"description":self.description,"lessons":[l.data() for l in self.lessons]}
class Lesson(db.Model):
    id=db.Column(db.Integer,primary_key=True); course_id=db.Column(db.Integer,db.ForeignKey("course.id"),nullable=False)
    title=db.Column(db.String(180),nullable=False); body=db.Column(db.Text,default=""); week_number=db.Column(db.Integer,default=1)
    def data(self): return {"id":self.id,"title":self.title,"body":self.body,"week_number":self.week_number}

class Event(db.Model):
    id=db.Column(db.Integer,primary_key=True); title=db.Column(db.String(180),nullable=False)
    description=db.Column(db.Text,default=""); starts_at=db.Column(db.String(40),nullable=False)
    meeting_url=db.Column(db.String(500),default=""); published=db.Column(db.Boolean,default=False)
    def data(self): return {k:getattr(self,k) for k in ["id","title","description","starts_at","meeting_url"]}

class MentorshipRequest(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    area=db.Column(db.String(120),nullable=False); goals=db.Column(db.Text,default="")
    status=db.Column(db.String(30),default="pending"); created_at=db.Column(db.DateTime,default=datetime.utcnow)
class PrayerRequest(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey("user.id"))
    message=db.Column(db.Text,nullable=False); visibility=db.Column(db.String(20),default="private")
    anonymous=db.Column(db.Boolean,default=False); status=db.Column(db.String(30),default="received")
    created_at=db.Column(db.DateTime,default=datetime.utcnow)
class Post(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    body=db.Column(db.Text,nullable=False); created_at=db.Column(db.DateTime,default=datetime.utcnow)
    author=db.relationship("User")
    def data(self): return {"id":self.id,"body":self.body,"author":self.author.name,"created_at":self.created_at.isoformat()}
class Comment(db.Model):
    id=db.Column(db.Integer,primary_key=True); post_id=db.Column(db.Integer,db.ForeignKey("post.id"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False); body=db.Column(db.Text,nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow)
class Article(db.Model):
    id=db.Column(db.Integer,primary_key=True); title=db.Column(db.String(180),nullable=False)
    category=db.Column(db.String(100),default="Lifestyle"); excerpt=db.Column(db.Text,default="")
    body=db.Column(db.Text,default=""); published=db.Column(db.Boolean,default=False)
    def data(self): return {k:getattr(self,k) for k in ["id","title","category","excerpt","body"]}
