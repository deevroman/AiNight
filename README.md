# AiNight
<p align="center">
<a href="https://heroku.com/deploy?template=https://github.com/deevroman/AiNight" target=”_blank”>
  <img src="https://www.herokucdn.com/deploy/button.svg" alt="Deploy">
</a>
</p>

### О решении

С помощью `OpenCV` выделяем лица на фото. После с помощью библиотеки `face_recognition` получаем вектор из 128 чисел, кодирующий лицо. Postgresql поддерживает данный тип данных и умеет эффективно работать с ним, а именно быстро искать максимально схожий вектор, т.е. лицо. Получив такой вектор от искомого лица и сделав сделав запрос на получение максимально схожего вектора получаем искомого человека. Собственно всё

## Варианты запуска:

### Jupyter notebook:
  Откройте `NotebookDemo.ipynb`. Если будете использовать Google Colab смените среду выполнения на GPU.  

### Heroku
  
  Нажмите на кнопку "Deploy to Heroku". Если приложение пишет, что не удалось сбросить базу, поробуйте ещё раз или обратитесь по адресу `/welcome`
### Локально
  
  Убедитесь, что порт 80 не занят apache/nginx/и т.п.
  
  ```bash
  pip install -r requirements.txt
  python wsgi_local.py  
  ```
  
### На сервере
  
  Можно на также как и локально, но это ненадёжно.
  
  Примерный процесс установки:

  ```bash
  pip install virtualenv
  cd AiNight
  virtualenv env
  source env/bin/activate
  pip install -r requirements.txt
  sudo apt-get install nginx
  sudo vim /etc/systemd/system/AiNight.service
  ```
  Далее везде вместо `USER` пользователь под которым вы хотите запускать сервис
  

  Запишите туда:
  ```
  [Unit]
  Description=wsgi for AiNight
  After=network.target
  [Service]
  User=USER
  Group=www-data
  WorkingDirectory=/home/USER/AiNight
  Environment="PATH=/home/USER/AiNight/env/bin"
  ExecStart=/home/USER/AiNight/env/bin/uwsgi --ini uWSGI.ini
  [Install]
  WantedBy=multi-user.target
  ```
  ```bash
  systemctl start AiNight
  systemctl enable AiNight
  ```
  
  ```bash
  sudo vim /etc/nginx/sites-available/AiNight
  ```
  
Запишите туда:

```
server {
    listen 0.0.0.0:8080;
    location / {
        client_max_body_size 5000M;
        client_body_buffer_size 50000k;
        include uwsgi_params;
        uwsgi_pass unix:/home/USER/AiNight/AiNight.sock;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/AiNight /etc/nginx/sites-enabled
systemctl restart nginx```
```

### Troubleshooting:

+ Библиотека `face_recognition` не поддерживает Windows. Используйте Linux/macOS 
+ Установка `dlib` долгая и нужно быть готовым, что вам может не хватить ОЗУ