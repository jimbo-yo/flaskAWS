from flask import Flask, request, render_template, jsonify
import mysql.connector
from config import DB_CONFIG
import boto3

app = Flask(__name__)

# Function to retrieve the MySQL credentials from AWS Secrets Manager
def get_secret():
    secret_name = "rds!db-f9022069-038a-45e7-82b6-b6d06d6332ca"  # Name of the secret in Secrets Manager
    region_name = "us-east-1"         # The AWS region where the secret is stored

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        # Fetch the secret from Secrets Manager
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response["SecretString"]
        return json.loads(secret)

    except ClientError as e:
        raise e

mysql_credentials = get_secret()

# Use the credentials in the application
DB_CONFIG = {
    'user': mysql_credentials["username"],
    'password': mysql_credentials["password"],
    'host': mysql_credentials["host"],
    'database': mysql_credentials["database"],


# Establish a MySQL connection
def get_db_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn

# Route for AWS infrastructure creation form
@app.route('/')
def form():
    return render_template('form.html')

# Example to create an S3 bucket based on form input
s3 = boto3.client('s3')

def create_s3_bucket(bucket_name):
    s3.create_bucket(Bucket=bucket_name)

@app.route('/submit', methods=['POST'])
def submit():
    app_name = request.form.get('app_name')
    aws_service = request.form.get('aws_service')

    if aws_service == 's3':
        create_s3_bucket(app_name)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert the form data into the MySQL database
    cursor.execute(
        "INSERT INTO aws_infrastructure (app_name, aws_service) VALUES (%s, %s)",
        (app_name, aws_service)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'status': 'success', 'message': 'Infrastructure details saved.'})

# Main function for local testing
if __name__ == '__main__':
    app.run(debug=True)
