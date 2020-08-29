from datetime import datetime, timedelta
from airflow.contrib.hooks.aws_hook import AwsHook
from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

class StageToRedshiftOperator(BaseOperator):
    ui_color = '#358140'
    template_fields = ("s3_key",)
    copy_sql = """
        COPY {}
        FROM '{}'
        ACCESS_KEY_ID '{}'
        SECRET_ACCESS_KEY '{}'
        FORMAT AS JSON '{}'
        REGION '{}';
    """
    
    @apply_defaults
    def __init__(self,
                 redshift_conn_id="",
                 aws_credentials_id="",
                 table="",
                 s3_bucket="",
                 s3_key="",
                 region="",
                 format_type="",
                 *args, **kwargs):

        super(StageToRedshiftOperator, self).__init__(*args, **kwargs)
        self.table = table
        self.redshift_conn_id = redshift_conn_id
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.format_type = format_type
        self.region = region
        self.aws_credentials_id = aws_credentials_id

    def execute(self, context):
        aws_hook = AwsHook(self.aws_credentials_id)
        credentials = aws_hook.get_credentials()
        redshift = PostgresHook(postgres_conn_id=self.redshift_conn_id)
        
        execution_ts = context.get("execution_date")
        now_minus2h_ts =datetime.now() - timedelta(hours=2)
        
        self.log.info('StageToRedshiftOperator not implemented yet')
        redshift.run("DELETE FROM {}".format(self.table))
        rendered_key = self.s3_key.format(**context)
        
        #code to determine if backfill on specifc timestamps is being requested
        if self.table == "staging_events" and execution_ts < now_minus2h_ts:
            s3_path = "s3://{}/{}/{}/{}/{}-{}-{}-events.json".format(self.s3_bucket, 
                                                                     rendered_key,
                                                                     execution_ts.strftime("%Y"),
                                                                     execution_ts.strftime("%m"),
                                                                     execution_ts.strftime("%Y"),
                                                                     execution_ts.strftime("%m"), 
                                                                     execution_ts.strftime("%d"))
            self.log.info("BACKFILL process in-progress: Copying data from S3 '{}' to '{}' table on Redshift".format(s3_path, self.table))
        else:
            s3_path = "s3://{}/{}".format(self.s3_bucket, rendered_key)
            self.log.info("Copying data from S3 '{}' to '{}' table on Redshift".format(s3_path, self.table))
         
        #code to determine S3 file path and the destination table on Redshift
        formatted_sql = StageToRedshiftOperator.copy_sql.format(
            self.table,
            s3_path,
            credentials.access_key,
            credentials.secret_key,
            self.format_type,
            self.region
        )
        redshift.run(formatted_sql)
        
        #clean up data to remove NULL values
        if self.table == "staging_events":
            redshift.run("DELETE FROM {} WHERE userId IS NULL;".format(self.table))
            redshift.run("DELETE FROM {} WHERE sessionId IS NULL;".format(self.table))
            redshift.run("DELETE FROM {} WHERE ts IS NULL;".format(self.table))
        else:
            redshift.run("DELETE FROM {} WHERE song_id IS NULL;".format(self.table))
            redshift.run("DELETE FROM {} WHERE artist_id IS NULL;".format(self.table))
