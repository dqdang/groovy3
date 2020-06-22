from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import joinedload, relationship, sessionmaker
from sqlalchemy import Table, Column, Integer, BigInteger, String, ForeignKey, Sequence

import os
import psycopg2
import sqlalchemy as sql

Base = declarative_base()

# heroku pg:psql -a groovy3
# import dburl
url = os.environ['DATABASE_URL']
engine = sql.create_engine(url, pool_size=17, client_encoding='utf8')


class Seen(Base):
    __tablename__ = "seen"
    id = Column(Integer, primary_key=True)
    timestamp = Column(String)


table_dict = {
    "Seen": Seen
}


def start_sess():
    Session = sessionmaker(bind=engine, autocommit=False)
    return Session()


def create_tables():
    sess = start_sess()
    Base.metadata.create_all(engine)
    sess.commit()
    sess.close()


def user_exists(user, sess=start_sess()):
    return sess.query(Seen).filter(Seen.unique_id == user).scalar()


def insert_user(value, timestamp):
    sess = start_sess()

    if user_exists(value, sess):
        sess.close()
        return False

    user = Seen(unique_id=value)
    user.timestamp = timestamp

    sess.add(user)
    sess.commit()
    sess.close()
    return True


""" Private getters """


def _get_object(table, sess=start_sess()):
    results = sess.query(table).all()
    return results


""" Public getters """


def get_table(table, column):
    sess = start_sess()
    results = sess.query(getattr(table_dict[table], column)).all()
    sess.close()
    return [] if len(results) == 0 else list(zip(*results))[0]


def get_timestamp(unique_id):
    sess = start_sess()
    user = user_exists(unique_id, sess)
    if user:
        rv = user.timestamp
        sess.close()
        return rv
    sess.close()
    return None


def change_timestamp(unique_id, timestamp):
    sess = start_sess()
    user = user_exists(unique_id, sess)

    if user:
        user.timestamp = timestamp
        sess.commit()
        sess.close()
        return True

    sess.close()
    return False


def delete_user(unique_id):
    sess = start_sess()
    user = user_exists(unique_id, sess)

    if user:
        sess.delete(user)
        sess.commit()
        sess.close()
        return True

    sess.close()
    return False
