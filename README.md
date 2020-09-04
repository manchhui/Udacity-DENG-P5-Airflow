# Udacity-DENG-P5-Data Pipelines with Airflow

## Introduction
A music streaming company, Sparkify, has decided that it is time to introduce more automation and monitoring to their data warehouse ETL pipelines and come to the conclusion that the best tool to achieve this is Apache Airflow.

As their data engineer they have set objectives to create high grade data pipelines that are dynamic and built from reusable tasks, can be monitored, and allow easy backfills. They have also noted that the data quality plays a big part when analyses are executed on the data warehouse and want to run tests against their datasets after the ETL steps have been executed to catch any discrepancies in the datasets.

The source data resides on AWS S3 and needs to be processed in Sparkify's data warehouse which resides on Amazon Redshift. The source datasets consist of JSON **logs** that tell them about user activity in the application and JSON metadata about the **songs** the users listen to.

* **s3://udacity-dend/song_data**: data about artists and songs, example of row '0' of the data as follows:
  `{0: {'artist_id': 'ARDR4AC1187FB371A1', 'artist_latitude': None, 'artist_location': '', 'artist_longitude': None, 'artist_name': 'Montserrat Caballé;Placido Domingo;Vicente Sardinero;Judith Blegen;Sherrill Milnes;Georg Solti', 'duration': 511.16363, 'num_songs': 1, 'song_id': 'SOBAYLL12A8C138AF9', 'title': 'Sono andati? Fingevo di dormire', 'year': 0}}`

* **s3://udacity-dend/log_data**: data of logs of usage of the app, example of row '0' of the data as follows:
  `{0: {'artist': 'Harmonia', 'auth': 'Logged In', 'firstName': 'Ryan', 'gender': 'M', 'itemInSession': 0, 'lastName': 'Smith', 'length': 655.77751, 'level': 'free', 'location': 'San Jose-Sunnyvale-Santa Clara, CA', 'method': 'PUT', 'page': 'NextSong','registration': 1541016707796.0, 'sessionId': 583, 'song': 'Sehr kosmisch', 'status': 200, 'ts': 1542241826796, 'userAgent': '"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/36.0.1985.125 Chrome/36.0.1985.125 Safari/537.36"', 'userId': '26'}}`

<br/>

> Apache Airflow is an open-source workflow management platform. It started at Airbnb in October 2014 as a solution to manage the company's increasingly complex workflows. Creating Airflow allowed Airbnb to programmatically author and schedule their workflows and monitor them via the built-in Airflow user interface. From the beginning, the project was made open source, becoming an Apache Incubator project in March 2016 and a Top-Level Apache Software Foundation project in January 2019.). [Wikipedia]

<br/>

## 1. Database Design Description
There are two source datasets, one called "song" and another "log". And from these two datasets the following star schema database will been created for optimized queries on song play analysis. The tables are as below:

### 1.1 Fact Table
The fact table in this star scheme will be named "songplays" and is designed to record "log" data associated with song plays. This fact table will have the
following columns: songplay_id, start_time, user_id, level, song_id, artist_id, session_id, location, user_agent, month and year. The month and year columns are used to partition the final table. 

### 1.2 Dimension Tables
The following tables in this star scheme are all dimension tables.
- users - This table will be used to record unique user details. This table will have the following columns:
            user_id, first_name, last_name, gender, level.
- songs - This table will be used to record unique song details. This table will have the following columns:
            song_id, title, artist_id, year, duration.
- artists - This table will be used to record unique artist details. This table will have the following columns:
            artist_id, name, location, latitude, longitude.
- time - This table will be used to record unique time details. This table will have the following columns: 
            start_time, hour, day, week, month, year, weekday

<br/>

## 2. Files in the repository
There are two source datasets, one called "song" and another "log" and these are located on the AWS S3 bucket as detailed in the introduction above. The following subsections contain brief descriptions of the rest of the files in this repository: 

### 2.1 Files within "/dags" folder:
#### 2.1.1 create_tables_dag.py
This **dag** must be used first before the **main dag** "udac_sl_etl_dag.py"

#### 2.1.2 udac_sl_etl_dag.py
This **main dag** contains all the operator calls and task dependencies to correctly perform ETL of the data from AWS S3 into the fact and dimension tables on AWS Redshift. , refer to the diagram below for the details of task dependencies.

![](https://github.com/manchhui/Udacity-DENG-P5-Airflow/blob/master/0F8A8AC5-6E35-40D6-B3B8-13A6489AE179_4_5005_c.jpeg)

Furthermore the default parameters are as below:
* The DAG does not have dependencies on past runs
* On failure, the task are retried 3 times
* Retries happen every 5 minutes
* Catchup is turned off
* Do not email on retry

### 2.2 Files within "/plugins/operators/" folder:
#### 2.2.1 stage_redshift.py
This python script is the stage operator and loads any JSON formatted, song and log, files from S3 to Amazon Redshift. The operator creates and runs a SQL COPY statement based on the parameters provided by the **main dag** "udac_sl_etl_dag.py" that calls this operator.

Additionally this operator contains a backfill feature that can load specific timestamped log files from S3 based on the execution time of the dag.

#### 2.2.2 load_dimension.py
This python script is the dimension operator and it utilises the **sql_queries.py** helper file to run data transformations. Dimension loads are loaded, based on the parameters provided by the **main dag** "udac_sl_etl_dag.py", with the truncate-insert pattern where the target table is emptied before the load. However a parameter exists that allows switching between insert mode or append mode when loading dimensions. 

#### 2.2.3 fact_dimension.py
This python script is the fact operator and it utilises the **sql_queries.py** helper file to run data transformations. Fact loads are loaded as append mode only.

#### 2.2.4 data_quality.py
The final operator is the data quality operator, which is used to run checks on the data itself. The operator's main functionality is to receive perform SQL based tests to ensure data has been copied and exists in each of the fact and dimension tables. The test result and expected result are checked and if there is no match, the operator will raise an exception.

### 2.3 File within "/plugins/helpers/" folder:
#### 2.3.1 sql_queries.py
This is called by the fact and load operators to perform ETL from the song and log staging tables to each of the fact and dimension tables.

<br/>

## 3. User Guide
### 3.1 Setup Airflow
To use the Airflow's UI you must first configure your AWS credentials and connection to Redshift.

> ##### 1. To go to the Airflow UI:
> * From within the Udacity Project Workspace, click on the blue Access Airflow button in the bottom right.
> * If you run Airflow locally, open http://localhost:8080 in Google Chrome (other browsers occasionally have issues rendering the Airflow UI).

> ##### 2. Click on the Admin tab and select Connections.

> ##### 3. Under Connections, select Create.

> ##### 4. On the create connection page, enter the following values:
> * Conn Id: Enter aws_credentials.
> * Conn Type: Enter Amazon Web Services.
> * Login: Enter your Access key ID from the IAM User credentials you downloaded earlier.
> * Password: Enter your Secret access key from the IAM User credentials you downloaded earlier.

> Once you've entered these values, select Save and Add Another.

> ##### 5. On the next create connection page, enter the following values:
> * Conn Id: Enter redshift.
> * Conn Type: Enter Postgres.
> * Host: Enter the endpoint of your Redshift cluster, excluding the port at the end. You can find this by selecting your cluster in the Clusters page of the Amazon Redshift console. See where this is located in the screenshot below. IMPORTANT: Make sure to NOT include the port at the end of the Redshift endpoint string.
> * Schema: Enter dev. This is the Redshift database you want to connect to.
> * Login: Enter awsuser.
> * Password: Enter the password you created when launching your Redshift cluster.
> * Port: Enter 5439.
> Once you've entered these values, select Save.


### 3.2 Running "udac_sl_etl_dag.py"
* Start the Airflow web server. 
* Once the Airflow web server is ready, access the Airflow UI. 
* First you MUST run "create_tables_dag.py" before "udac_sl_etl_dag.py" to ensure all the staging, fact and dimension tables are created before data can be loaded into them.


