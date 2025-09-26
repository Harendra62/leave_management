import os
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables from both .env and env.local files
load_dotenv()

class Settings:
    ENV: str = os.getenv('ENV', 'development')
    MYSQL_USER: str = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD: str = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_HOST: str = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT: str = os.getenv('MYSQL_PORT', '3306')
    MYSQL_DB: str = os.getenv('MYSQL_DB', 'transcribe_dev')
    AWS_SECRET_NAME: str = os.getenv('AWS_SECRET_NAME', 'prod/mysql')
    AWS_REGION: str = os.getenv('AWS_REGION', 'eu-west-1')
    S3_BUCKET_NAME: str = "primumai" 
    
    # Timezone configuration
    TIMEZONE: str = os.getenv('TIMEZONE', 'Europe/Dublin')
    

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        if self.ENV == 'production':
            prod_db: str = os.getenv('MYSQL_DB', 'transcribe_dev')
            creds = get_aws_secret(self.AWS_SECRET_NAME, self.AWS_REGION)
            print(creds,"================")
            print(creds,"================")
            return f"mysql+pymysql://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}/{prod_db}"
        else:
            return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

@lru_cache
def get_settings():
    return Settings()

 