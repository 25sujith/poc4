from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from pyspark.sql import SparkSession  # Import SparkSession
from pyspark.sql.functions import col
from airflow.operators.email_operator import EmailOperator

default_args={
        'owner':'sujith',
        'email' :['inkulusujith5@gmail.com'],
        'email_on_failure': False,
        'email_on_retry': False,
        'retries':3,
        'retry_delay':timedelta(minutes=5)
        }


credit_card_fraud_detection1 = DAG(
    'credit_card_fraud_detection1',
    default_args=default_args,
    description='credit_card_fraud_detection1',
    start_date=datetime(2023, 9, 23),  # Corrected placement of 'start_date'
    schedule_interval='* * * * *',
    catchup=False,
    tags=['example', 'helloworld']
)


# Task 1: Dummy Operator to start the task
task1 = DummyOperator(task_id='start_task', dag=credit_card_fraud_detection1)

def run_spark_job():

    spark = SparkSession.builder.appName("AirflowProject").getOrCreate()

    data = spark.read.option("header", "true").csv("/usr/local/lib/python3.8/dist-packages/airflow/example_dags/inputcfile/CreditCard.csv")
    data1 = spark.read.option("header", "true").csv("/usr/local/lib/python3.8/dist-packages/airflow/example_dags/inputcfile/CityList.csv")
    data2 = spark.read.option("header", "true").csv("/usr/local/lib/python3.8/dist-packages/airflow/example_dags/inputcfile/CountryList.csv")
    
    data.createOrReplaceTempView("transactions")
    data1.createOrReplaceTempView("locations")
    data2.createOrReplaceTempView("CountryList")


    joineddata = spark.sql("""
    SELECT transactions.id AS transaction_id,transactions.Time,transactions.Class,transactions.Amount,locations.id AS location_id,locations.name,locations.alpha2
    FROM transactions
    INNER JOIN locations
    ON transactions.id = locations.id
    """)
    fraudulentactivitiesquery = """
    SELECT
    transaction_id,
    name,
    alpha2,
    from_unixtime(Time) as timestamp,
    Amount,
    Class
    FROM joineddata
    WHERE Class = 1
    """

    fraudulent_activities = spark.sql(fraudulentactivitiesquery)
    fraudulent_activities.createOrReplaceTempView("fraudulentactivities")

    fraudulent_activities1 = spark.sql("""
    SELECT fraudulentactivities.transaction_id, fraudulentactivities.timestamp, fraudulentactivities.Class,
           fraudulentactivities.Amount, fraudulentactivities.name, fraudulentactivities.alpha2 AS fraudulentactivities_alpha2,
           CountryList.alpha2 AS CountryList_alpha2, CountryList.companyen
    FROM  fraudulentactivities
    JOIN  CountryList
    ON  fraudulentactivities.alpha2=CountryList.alpha2
    """)

    fraudulent_activities1.createOrReplaceTempView("fraudulent_activities1")

    fraudulent_activities1.write.csv("usr/local/lib/python3.8/dist-packages/airflow/example_dags/inputcfile/outputfile", header=True, mode="overwrite")
task2 = PythonOperator(
        task_id='run_spark_job',
        python_callable=run_spark_job,
        dag=credit_card_fraud_detection1)

task3 = DummyOperator(task_id='end_task', dag=credit_card_fraud_detection1)
email_task = EmailOperator(
    task_id="email_task",
    to=['inkulusujith5@gmail.com'],
    subject="Airflow successful!",
    html_content="<i>Message from Airflow --> the output file is generated</i>",
    dag=credit_card_fraud_detection1  # Don't forget to specify the DAG
)
# Define task dependencies
task1 >> task2 >> task3 >>email_task
