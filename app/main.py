from flask import Flask, render_template, redirect
from flask import request
from flask_cors import CORS, cross_origin
import psycopg2
import sys
import dlib
import cv2
import face_recognition
import os
import random
import imghdr

DATABASE_URL = os.environ.get('DATABASE_URL', None)
app = Flask(__name__, static_folder='static')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

connection_db = psycopg2.connect(DATABASE_URL)
connection_db.autocommit = True

class FaceNotFound(Exception):
    pass


def check_photo(file_name):
    if imghdr.what(file_name) is None:
        raise Exception("Bad photo")


def save_img(file_name, name):
    check_photo(file_name)
    try:
        image = cv2.imread(file_name)
    except cv2.error as e:
        raise Exception('Bad photo')
    face_detector = dlib.get_frontal_face_detector()
    detected_faces = face_detector(image, 1)
    print("Found {} faces in the image file {}".format(len(detected_faces), file_name))
    if len(detected_faces) == 0:
        raise FaceNotFound("На фото нет лица")
    for i, face_rect in enumerate(detected_faces):
        print("- Face #{} found at Left: {} Top: {} Right: {} Bottom: {}".format(i, face_rect.left(), face_rect.top(),
                                                                                 face_rect.right(), face_rect.bottom()))
        crop = image[face_rect.top():face_rect.bottom(), face_rect.left():face_rect.right()]
        encodings = face_recognition.face_encodings(crop)
        # print(encodings)
        if len(encodings) > 0:
            db = connection_db.cursor()
            try:
                query = "SELECT count(*) FROM vectors WHERE file='{}'".format(name)
                db.execute(query)
                if db.fetchone()[0] > 0:
                    raise Exception("Такой name уже есть")
                query = "INSERT INTO vectors (file, vec_low, vec_high) VALUES ('{}', CUBE(array[{}]), CUBE(array[{}]));".format(
                    name,
                    ','.join(str(s) for s in encodings[0][0:63]),
                    ','.join(str(s) for s in encodings[0][64:127]),
                )
                db.execute(query)
                # print(query)
                connection_db.commit()
            finally:
                db.close()
        else:
            raise FaceNotFound("На фото нет лица")


def find_face(file_name):
    check_photo(file_name)
    try:
        image = cv2.imread(file_name)
    except cv2.error as e:
        raise Exception('Bad photo')
    face_detector = dlib.get_frontal_face_detector()
    detected_faces = face_detector(image, 1)
    print("Found {} faces in the image file {}".format(len(detected_faces), file_name))
    if len(detected_faces) == 0:
        raise FaceNotFound("На фото нет лица")
    for i, face_rect in enumerate(detected_faces):
        print("- Face #{} found at Left: {} Top: {} Right: {} Bottom: {}".format(i, face_rect.left(), face_rect.top(),
                                                                                 face_rect.right(), face_rect.bottom()))
        crop = image[face_rect.top():face_rect.bottom(), face_rect.left():face_rect.right()]

        encodings = face_recognition.face_encodings(crop)
        if len(encodings) > 0:
            db = connection_db.cursor()
            query = "SELECT file FROM vectors ORDER BY " + \
                    "(CUBE(array[{}]) <-> vec_low) + (CUBE(array[{}]) <-> vec_high) ASC LIMIT 1 ;".format(
                        ','.join(str(s) for s in encodings[0][0:63]),
                        ','.join(str(s) for s in encodings[0][64:127]),
                    )
            #             print(query)
            db.execute(query)
            print("The number of parts: ", db.rowcount)
            row = db.fetchone()

            while row is not None:
                print(row)
                db.close()
                return row[0]
                # row = db.fetchone()
            raise FaceNotFound("Не найдено похожих лиц")
        else:
            raise FaceNotFound("На фото нет лица")


def get_db_size():
    db = connection_db.cursor()
    query = "SELECT count(*) from vectors"
    db.execute(query)
    row = db.fetchone()
    db.close()
    return row[0]


@app.route('/get_count_faces', methods=['GET'])
@cross_origin()
def route_get_db_size():
    return get_db_size()


@app.route('/find_face', methods=['POST'])
@cross_origin()
def get_find_face():
    path = "app/tmp/" + str(random.randint(1, 1000000))
    request.files['image'].save(path)
    try:
        return find_face(path), 200
    except FaceNotFound as e:
        return str(e) + "</br>Количество лиц  базе: " + str(get_db_size()), 200
    except Exception as e:
        return str(e), 200


@app.route('/add_face', methods=['POST'])
@cross_origin()
def post_save_face():
    name = request.form['name']
    path = "app/tmp/" + name
    if len(name) > 255:
        return "Long name", 200
    for i in name:
        if i.lower() not in 'abcdefghijklmnopqrstuvwxyz0123456789_абвгдеёжзийклмнопрстуфхцчшщъыьэюя':
            return "Invalid name", 200
    request.files['image'].save(path)
    try:
        save_img(path, name)
    except Exception as e:
        return str(e), 200
    if get_db_size() > 2000:
        reset()
        return "ok. database reset. Reason: size > 2000", 200
    return name + " сохранён в базу", 200


def init():
    save_img("app/photos/navalny.jpg", "navalny")
    save_img("app/photos/putin.jpg", "putin")
    save_img("app/photos/solovei.jpg", "solovei")
    save_img("app/photos/zelen.jpg", "zelen")


@app.route('/reset', methods=['GET'])
@cross_origin()
def reset():
    try:
        db = connection_db.cursor()
        try:
            query = "TRUNCATE vectors"
            db.execute(query)
            connection_db.commit()
            init()
        finally:
            db.close()
    except Exception as e:
        print(e)
        return "Не удалось", 200
    return "Сброшено", 200


@app.route('/print_db', methods=['GET'])
@cross_origin()
def print_db():
    db = connection_db.cursor()
    try:
        query = "SELECT file from vectors"
        db.execute(query)
        ans = ""
        row = db.fetchone()
        while row is not None:
            ans += row[0] + "</br>"
            row = db.fetchone()
    finally:
        db.close()
    return ans, 200


@app.route('/test/<int:pic_id>', methods=['GET'])
@cross_origin()
def test(pic_id):
    try:
        if pic_id == 1:
            return find_face("app/test/navalny.jpg")
        elif pic_id == 2:
            return find_face("app/test/solovei.jpg")
        elif pic_id == 3:
            return find_face("app/test/putin.jpg")
        elif pic_id == 4:
            return find_face("app/test/zelen.jpg")
    except FaceNotFound as e:
        return str(e) + "</br>Количество лиц  базе: " + str(get_db_size()), 200
    except Exception as e:
        return str(e), 200
    return "", 200


@app.route('/welcome')
def welcome():
    db = connection_db.cursor()
    db.execute('create extension if not exists cube;')
    db.execute('drop table if exists vectors;')
    db.execute('create table vectors (id serial, file varchar, vec_low cube, vec_high cube);')
    db.execute('create index vectors_vec_idx on vectors (vec_low, vec_high);')
    db.close()
    redirect("/")


@app.route('/')
def index():
    return render_template('index.html')
