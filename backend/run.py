import os, click
from getpass import getpass
from dotenv import load_dotenv
load_dotenv()
from app import create_app, db
from app.models import User, Devotional, Course, Lesson, Event, Article
app = create_app()

@app.cli.command("create-admin")
def create_admin():
    email = input("Admin email: ").strip().lower()
    name = input("Admin full name: ").strip()
    password = getpass("Password (minimum 10 characters): ")
    if len(password) < 10:
        raise click.ClickException("Password must be at least 10 characters.")
    if User.query.filter_by(email=email).first():
        raise click.ClickException("That email is already registered.")
    user = User(name=name, email=email, role="admin", status="approved")
    user.set_password(password)
    db.session.add(user); db.session.commit()
    click.echo("Administrator created. Sign in through the web app.")

@app.cli.command("seed")
def seed():
    if not Devotional.query.first():
        db.session.add(Devotional(date="2026-01-01", verse="Be strong and of a good courage.", reference="Joshua 1:9", reflection="God's presence gives courage for each step.", prayer="Lord, strengthen my heart today.", action="Take one purposeful step in faith.", published=True))
    if not Course.query.first():
        c = Course(title="Growing in Faith and Purpose", description="A foundational self-paced course for personal and spiritual growth.", published=True)
        db.session.add(c); db.session.flush()
        db.session.add(Lesson(course_id=c.id, title="Growing in Your Personal Relationship with God", body="Build a consistent relationship with God through prayer, Scripture, reflection and obedience.", week_number=1))
    if not Event.query.first():
        db.session.add(Event(title="Sisterhood Live Gathering", description="A welcoming online gathering for encouragement and conversation.", starts_at="2027-01-09T16:00:00", meeting_url="", published=True))
    if not Article.query.first():
        db.session.add(Article(title="The Woman Beyond the Pulpit", category="My Life, My Story", excerpt="Your identity, gifts and dreams remain valuable beyond ministry responsibilities.", body="There is a woman behind every ministry assignment. Her dreams, interests, friendships and aspirations deserve room to grow. Beyond the Pulpit celebrates the complete woman.", published=True))
    db.session.commit()
    click.echo("Sample content seeded.")

if __name__ == "__main__":
    app.run()
