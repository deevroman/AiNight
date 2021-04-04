from flask import Flask
from flask import request
from flask_cors import CORS, cross_origin
import psycopg2
import sys
import dlib
import cv2
import face_recognition
import os
import random

host = os.environ.get('STORAGE_HOST', None)
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

connection_db = psycopg2.connect("user='aires4' password='aires4' host='{}' dbname='postgres'".format(host))


def save_img(file_name, name):
    face_detector = dlib.get_frontal_face_detector()
    image = cv2.imread(file_name)
    detected_faces = face_detector(image, 1)
    print("Found {} faces in the image file {}".format(len(detected_faces), file_name))
    for i, face_rect in enumerate(detected_faces):
        print("- Face #{} found at Left: {} Top: {} Right: {} Bottom: {}".format(i, face_rect.left(), face_rect.top(),
                                                                                 face_rect.right(), face_rect.bottom()))
        crop = image[face_rect.top():face_rect.bottom(), face_rect.left():face_rect.right()]
        encodings = face_recognition.face_encodings(crop)
        print(encodings)
        if len(encodings) > 0:
            db = connection_db.cursor()
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
        else:
            raise Exception("На фото нет лица")


def find_face(file_name):
    face_detector = dlib.get_frontal_face_detector()
    image = cv2.imread(file_name)
    detected_faces = face_detector(image, 1)

    print("Found {} faces in the image file {}".format(len(detected_faces), file_name))
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
                return row[0]
                row = db.fetchone()

        #             db.close()
        else:
            raise Exception("На фото нет лица")


def get_db_size():
    db = connection_db.cursor()
    query = "SELECT count(*)"
    db.execute(query)
    return db.fetchone()[0]


@app.route('/get_count_faces', methods=['GET'])
@cross_origin()
def route_get_db_size():
    return get_db_size()


@app.route('/find_face', methods=['POST'])
@cross_origin()
def get_find_face():
    path = "app/tmp/" + str(random.randint(1, 100000))
    request.files['image'].save(path)
    try:
        return find_face(path), 200
    except:
        return "bad", 200


@app.route('/add_face', methods=['POST'])
@cross_origin()
def post_save_face():
    name = request.form['name']
    path = "app/tmp/" + name
    for i in name:
        if i.lower() not in 'abcdefghijklmnopqrstuvwxyz0123456789_абвгдеёжзийклмнопрстуфхцчшщъыьэюя':
            return "Invalid path", 200
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
    try:
        save_img("app/photos/navalny.jpg", "navalny")
        save_img("app/photos/putin.jpg", "putin")
        save_img("app/photos/solovei.jpg", "solovei")
        save_img("app/photos/zelen.jpg", "zelen")
    except Exception as e:
        return str(e), 200
    return "Сброшено", 200


@app.route('/reset', methods=['GET'])
@cross_origin()
def reset():
    db = connection_db.cursor()
    query = "TRUNCATE vectors"
    db.execute(query)
    connection_db.commit()
    init()
    return "Сброшено", 200


@app.route('/test/<int:pic_id>', methods=['GET'])
@cross_origin()
def test(pic_id):
    if pic_id == 1:
        return find_face("app/test/navalny.jpg")
    elif pic_id == 2:
        return find_face("app/test/putin.jpg")
    elif pic_id == 3:
        return find_face("app/test/solovei.jpg")
    elif pic_id == 4:
        return find_face("app/test/zelen.jpg")
    return "", 200


@app.route('/')
def index():
    return "<h1>KEK</h1>"
