# AiNight
<p align="center">
<a href="https://heroku.com/deploy?template=https://github.com/deevroman/AiNight">
  <img src="https://www.herokucdn.com/deploy/button.svg" alt="Deploy">
</a>
</p>

###О решении. 

С помощью `OpenCV` выделяем лица на фото. После с помощью библиотеки `face_recognition` получаем вектор из 128 чисел, кодирующий лицо. Postgresql поддерживает данный тип данных и умеет эффективно работать с ним, а именно быстро искать максимально схожий вектор, т.е. лицо. Получив такой вектор от искомого лица и сделав сделав запрос на получение максимально схожего вектора получаем искомого человека. Собственно всё

###Варианты запуска:

+ В jupyter notebook:
+ Heroku
+ Локально
+ На сервере

###Troubleshooting:

+ Библиотека `face_recognition` не поддерживает Windows. Используйте Linux/macOS 
+ Установка `dlib` долгая и нужно быть готовым, что вам может не хватить ОЗУ
