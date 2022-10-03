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

