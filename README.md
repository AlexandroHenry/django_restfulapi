# django_server

# 오라클 서버 접속
#### ssh ubuntu@131.186.28.79

# ssh 내에서
#### su - root

# 서버 유지하는 방법
#### screen
#### ctrl a -> D

# How to see the version of package installed in django
#### pip list -v

# Virtual Environment
#### sudo pip3 install virtualenv
#### virtualenv venv
#### source newenv/bin/activate
#### pip3 install django

# pip installation guide
 #### pip3 install django
 #### pip3 install yfinance
 #### pip3 install djangorestframework
 #### pip3 install dnspython
 #### pip3 install django-cors-headers
 #### pip3 install uwsgi
 #### pip3 install Pillow

# Crontab
#### pip3 install django-crontab

### Settings.py

#### INSTALLED_APPS = (
####    'django_crontab',
####    ...
#### )

#### CRONJOBS = [                                              크론탭 로그만들기
####    ('*/5 * * * *', 'myapp.cron.my_scheduled_job', '>> /tmp/scheduled_job.log')
#### ]

### app/cron.py
#### def my_scheduled_job():
####    print("hello")

####    *　　　　　　  *　　　　　　*　　　　　　*　　　　　　* 
#### 분(0-59)　　시간(0-23)　　일(1-31)　　월(1-12)　　　요일(0-7)

#### Cronjob 올리기
#### python manage.py crontab add

#### Cronjob 올라간것 확인하기
#### python manage.py crontab show

#### Cronjob 올라간것 전체 삭제하기
#### python manage.py crontab remove

# To avoid djongo error
#### pip3 install djongo==1.3.6
#### pip3 install pymongo==3.12.3

# django_api

# kill Port
#### sudo kill -9 `sudo lsof -t -i:80`


# 가상환경 만들어주기
#### python3 -m venv 가상환경명

# 가상환경 실행하기
#### source 가상환경폴더/bin/activate

# NGINX
#### sudo apt-get purge nginx nginx-common nginx-full
#### sudo apt-get install nginx



# gunicorn을 통한 django nginx 연동하기
#### sudo apt update
#### sudo apt upgrade
#### sudo apt install python3-pip

#### Virtualenv 설치 및 실행 후
#### Django 설치

#### djangoadmin startproject 프로젝트이름
#### 프로젝트 실행 해보기

#### pip3 install gunicorn
#### gunicorn --bind 0:80 프로젝트명.wsgi:application

### Gunicorn 서비스등록
#### sudo vi /etc/systemd/system/gunicorn.service

### 파일 내용
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/root/django_restfulapi (프로젝트 루트 주소를 적어줍니다 (pwd 로 루트 주소 확인 가능))
ExecStart=/root/django_restfulapi/venv/bin/gunicorn --bind 0.0.0.0:80 프로젝트명.wsgi:application

[Install]
WantedBy=multi-user.target

#### sudo systemctl daemon-reload
#### sudo systemctl start gunicorn
#### sudo systemctl enable gunicorn
#### sudo systemctl status gunicorn.service

### NGINX 설치 및 실행
#### sudo apt-get install nginx
#### systemctl start nginx

### NGINX & Django 연동
#### vi /etc/nginx/nginx.conf

### 파일내용
http {
    include /etc/nginx/conf.d/*.conf;  (이부분만 바꿔주면 됩니다. 아래 몇줄은 그냥 이게 대충 어디인지 확인하려고 쓴거임)
    default_type application/octet-stream;

    ##
    # SSL Settings
}

#### vi /etc/nginx/conf.d/default.conf
### 파일내용
server {
	listen 80;
	server_name 0.0.0.0;

	location / {
		include proxy_params;
		proxy_pass http://0.0.0.0:80;
	}
}

#### service nginx restart

### 참고 : https://www.youtube.com/watch?v=nGoA1R1_pR0