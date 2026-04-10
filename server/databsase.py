import pymysql
from config import MYSQL_CONFIG


def get_conn():
    return pymysql.connect(
        host=MYSQL_CONFIG["host"],
        port=MYSQL_CONFIG["port"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        database=MYSQL_CONFIG["database"],
        charset=MYSQL_CONFIG["charset"],
        autocommit=True
    )


def query_one(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()
    finally:
        conn.close()


def query_all(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()


def execute(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            rows = cursor.execute(sql, params or ())
            return rows
    finally:
        conn.close()

def insert_and_get_id(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()