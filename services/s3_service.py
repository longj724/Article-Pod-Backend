import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client('s3',
                                      aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                      aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                                      region_name=os.getenv('AWS_REGION'))
        self.bucket_name = os.getenv('AWS_BUCKET_NAME')

    def upload_file(self, file_path: str, object_name: str) -> str:
        """
        Upload a file to S3 bucket and return the URL
        """
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)

            print(f"Uploaded file to S3: {file_path} with filename: {object_name}")

            url = self.get_file_url(object_name)
            return url
        except (NoCredentialsError, PartialCredentialsError) as e:
            print(f"Credentials error: {str(e)}")
            raise

    def get_file_url(self, file_name):
        return f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{file_name}"