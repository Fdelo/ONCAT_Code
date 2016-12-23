##########################################################################
# Import modules
##########################################################################

from functools import wraps
import json
import gc
import sys
import traceback

from flask import Flask, render_template, request, url_for, redirect, session, flash, jsonify

from wtforms import Form, StringField, PasswordField, validators
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart

# User-defined modules
from dbconnect import connection
from table_list import set_tables

# Define the app object
app = Flask(__name__)


@app.errorhandler(400)
def four_hundred_err(e):
    return render_template('400.html', error=e)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')


@app.errorhandler(500)
def five_hundred_err(e):
    return render_template('500.html', error=e)


def login_req(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)

        else:
            flash("You need to login first.")
            return redirect(url_for('login_page'))

    return wrap


# route to the home page
@app.route('/')
def homepage():
    return render_template('main.html')


# route to the course page
@app.route('/course/', methods=["GET"])
@login_req
def course():
    error = None
    try:
        dc, c, conn = connection()
        parent_table, child_table, map_table = set_tables(session['user_university'])
        user_id = session['user_id']

        parent_course_dict = {}
        child_course_dict = {}
        map_dict = {}

        '''
        Get all the parent courses
        '''
        sql = 'SELECT DISTINCT `' + parent_table + '_course#` FROM ' + map_table + '_map'
        c.execute(sql)
        for row in c:
            parent_course_dict[row[0]] = []

        for key, value in parent_course_dict.iteritems():
            sql = 'SELECT course_desc FROM ' + parent_table + '_courses WHERE `course#` = (%s)'
            c.execute(sql, [key])
            value.append(c.fetchone()[0])
            sql = 'SELECT learning_outcome FROM ' + parent_table + '_course_outcomes WHERE `course#` = (%s)'
            c.execute(sql, [key])
            learning_outcomes = [item[0] for item in c.fetchall()]
            value.append(learning_outcomes)

        '''
        Get all the child courses
        '''
        sql = 'SELECT DISTINCT `' + child_table + '_course#` FROM ' + map_table + '_map'
        c.execute(sql)
        for row in c:
            child_course_dict[row[0]] = []

        for key, value in child_course_dict.iteritems():
            sql = 'SELECT course_desc FROM ' + child_table + '_courses WHERE `course#` = (%s)'
            c.execute(sql, [key])
            value.append(c.fetchone()[0])
            sql = 'SELECT learning_outcome FROM ' + child_table + '_course_outcomes WHERE `course#` = (%s)'
            c.execute(sql, [key])
            learning_outcomes = [item[0] for item in c.fetchall()]
            value.append(learning_outcomes)

        '''
        Map the courses
        '''
        # iterate through the parent courses(keys in the dict)
        for pc in parent_course_dict.keys():
            sql = 'SELECT approval, comments FROM ' + map_table + '_approvals WHERE `course#` = (%s) AND uid = (%s)'
            c.execute(sql, [pc, user_id])
            r = c.fetchone()
            if r <= 0:
                r = [None, '']
                sql = 'INSERT INTO ' + map_table + '_approvals (approval, comments, `course#`, uid) VALUES (%s, %s, %s, %s)'
                c.execute(sql, [r[0], r[1], pc, session['user_id']])
                conn.commit()

            map_dict[pc] = [[pc, parent_course_dict[pc][0], parent_course_dict[pc][1], r[0], r[1]]]
            sql = 'SELECT mapID, `' + child_table + '_course#` FROM ' + map_table + '_map WHERE `' + parent_table + '_course#` = (%s)'
            c.execute(sql, [pc])
            for row in c:
                temp_list = []  # used to store child course info neatly
                temp_list.extend((row[1], child_course_dict[row[1]][0], child_course_dict[row[1]][1]))
                sql = 'SELECT rating, comments FROM ' + map_table + '_ratings WHERE mapID = (%s) AND uid = (%s)'
                c.execute(sql, [row[0], user_id])
                r = c.fetchone()
                if r <= 0:
                    r = [0, '']
                    sql = 'INSERT INTO ' + map_table + '_ratings (rating, comments, mapID, uid) VALUES (%s, %s, %s, %s)'
                    c.execute(sql, [0, '', row[0], session['user_id']])
                    conn.commit()

                temp_list.extend((r[0], r[1]))
                map_dict[pc].append(temp_list)

        return render_template(
            'course.html',
            map_dict=map_dict
            )

    except Exception as e:
        flash(str(e))
        flash(sys.exc_traceback.tb_lineno)
        return render_template('course.html')


@app.route("/post_json/", methods=["POST"])
def post_json():
    try:
        if request.method == "POST":
            dc, c, conn = connection()
            parent_table, child_table, map_table = set_tables(session['user_university'])
            if request.form.get('classname') == 'pforms':
                courses = request.form.get('formkeys')
                percent = int(request.form.get('percent'))
                comments = request.form.get('comment')
                childcourse, parentcourse = courses.split("|")

                sql = 'SELECT mapID FROM ' + map_table + '_map where `' + parent_table + '_course#` = (%s) AND `' + child_table + '_course#` = (%s)'
                c.execute(sql, [parentcourse, childcourse])
                map_id = c.fetchone()[0]

                # Select the rating based on mapid
                sql = 'SELECT * FROM ' + map_table + '_ratings \
                        WHERE mapID = (%s) AND uid = (%s)'

                data = c.execute(sql, [map_id, session['user_id']])
                if data > 0:
                    sql = 'UPDATE ' + map_table + '_ratings SET rating = (%s), comments = (%s) WHERE mapID = (%s) AND uid = (%s)'
                    data = c.execute(sql, [
                        percent, thwart(comments), map_id, session['user_id']
                    ])
                    conn.commit()
                    return jsonify(success=True)

            elif request.form.get('classname') == 'aforms':
                coursename = request.form.get('coursename')
                if request.form.get('choice') == 'Yes':
                    approval = 1
                else:
                    approval = 0

                comments = request.form.get('comment')
                sql = 'UPDATE ' + map_table + '_approvals SET approval = (%s), comments = (%s) WHERE (`course#` = (%s) AND uid = (%s))'
                c.execute(sql, [approval, thwart(comments), coursename, session['user_id']])
                conn.commit()
                return jsonify(success=True)

            return jsonify(success=False)
    except Exception as e:
        return flash(str(e))


@app.route("/logout/")
@login_req
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('login_page'))


@app.route('/login/', methods=["GET", "POST"])
def login_page():
    error = None
    try:
        dc, c, conn = connection()
        if request.method == "POST":
            sql = "SELECT * FROM user WHERE email = (%s)"
            data = c.execute(sql, [thwart(request.form['email'])])
            r = c.fetchone()
            if request.form['password'] == r[2]:
                session['logged_in'] = True
                session['email'] = request.form['email']
                session['user_id'] = r[0]
                session['user_university'] = r[3]
                return redirect(url_for("course"))

            else:
                error = "Invalid credentials. Try again"

        gc.collect()

        return render_template("login.html", error=error)

    except Exception as e:
        error = "Invalid credentials. Try again"
        return render_template("login.html", error=error)


if __name__ == "__main__":
    app.secret_key = '\x96jF\xe7\xde\xe9 ]\x12C\x88\xaf\xf7W\xd5\xfdf\x87\xb1\x88xq\xff\x0f\xa3\x82\xaf=\xf6\xbe\xcd\x90\xcd\x92\x8c\xf4i\xa7\x7f\x8c'
    app.run()
