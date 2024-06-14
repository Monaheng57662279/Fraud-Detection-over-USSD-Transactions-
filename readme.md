
1)  ## First  Create virtualenvironment with following COMMAND:-

        virtualenv venv

 NOTE:- venv is name of name of virtualenvironment. we can give any name which we want.

2) Then Activate venv:-

        source venv/bin/activate

3) ## Then Install requirements.txt with following COMMAND:-

        pip install -r requirements.txt


4)  ## create superuser by following COMMAND in your root directory:-

        python3 manage.py createsuperuser

5)  ## Then start your server by typing following COMMAND:-

        python3 manage.py runserver

    NOTE:- If you are adding some model in models.py or changing something don't forget to make migrations 

        python3 manage.py makemigrations

    and migrate it to databasesudo service cups stop

        python3 manage.py migrate

6)    ## IF apache server status is stopped. 
              ## start server  
        sudo systemctl start kafka
        sudo systemctl start zookeeper
            ##check server status
        sudo systemctl status zookeeper
        sudo systemctl status kafka

7)  ## to run consumer and producer scripts
        python3 manage.py produce_data
        python3 manage.py run_consumer


