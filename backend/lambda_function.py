import json
import os
import boto3

# ==============================================================================
# AWS Lambda Backend Controller for Serverless Web Application
# ==============================================================================
# This Lambda function acts as the backend server behind AWS API Gateway.
# It performs two primary tasks:
#   1. Routing HTTP GET requests: Serves 'contactus.html' directly to the browser
#   2. Routing HTTP POST requests: Inserts user form data into Amazon DynamoDB,
#      then returns 'success.html' as a confirmation page.
# ==============================================================================

def lambda_handler(event, context):
    """
    Main entry point executed by AWS Lambda whenever an HTTP request arrives from API Gateway.
    
    Parameters:
      event (dict): Contains HTTP request details passed by API Gateway, such as:
                    - event['httpMethod']: The HTTP verb ('GET' or 'POST')
                    - event['queryStringParameters']: Any URL query parameters
                    - event['body']: The submitted form data
      context (LambdaContext): Runtime information about the Lambda function execution.
      
    Returns:
      dict: Standard API Gateway proxy response with statusCode, headers, and body.
    """
    try:
        # Route the request based on HTTP method, query parameters, and form payload
        mypage = page_router(event['httpMethod'], event['queryStringParameters'], event['body'])
        return mypage
    except Exception as e:
        # If an unhandled exception occurs, return HTTP 500 with the error description
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def page_router(httpmethod, querystring, formbody):
    """
    Acts as a lightweight serverless web router.
    
    Parameters:
      httpmethod (str): 'GET' or 'POST'
      querystring (dict or None): Dictionary of query parameters
      formbody (str): URL-encoded string submitted from the HTML contact form
      
    Returns:
      dict: API Gateway response dictionary with Content-Type text/html
    """
    # --------------------------------------------------------------------------
    # 1. HANDLE GET REQUESTS (User visits the API Gateway URL in their browser)
    # --------------------------------------------------------------------------
    if httpmethod == 'GET':
        try:
            # Read and serve the contact registration form (contactus.html)
            with open('contactus.html', 'r') as htmlFile:
                htmlContent = htmlFile.read()

            # Return HTTP 200 OK with the HTML content for browser rendering
            return {
                'statusCode': 200,
                'headers': {"Content-Type": "text/html"},
                'body': htmlContent
            }
        except Exception as e:
            # If the file could not be read or does not exist, return HTTP 500
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }

    # --------------------------------------------------------------------------
    # 2. HANDLE POST REQUESTS (User submitted the registration form)
    # --------------------------------------------------------------------------
    elif httpmethod == 'POST':
        try:
            # Insert the submitted form data into the Amazon DynamoDB table
            insert_record(formbody)

            # Read and serve the confirmation page (success.html)
            with open('success.html', 'r') as htmlFile:
                htmlContent = htmlFile.read()

            # Return HTTP 200 OK with the success page
            return {
                'statusCode': 200,
                'headers': {"Content-Type": "text/html"},
                'body': htmlContent
            }
        except Exception as e:
            # Return HTTP 500 if the DynamoDB insert or file read fails
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }


def insert_record(formbody):
    """
    Parses the URL-encoded form data and persists the record into Amazon DynamoDB
    using a PartiQL (SQL-compatible query language for DynamoDB) statement.
    
    Parameters:
      formbody (str): Example: "fname=John&lname=Doe&email=john@example.com&message=Hello"
      
    Returns:
      dict: Response returned by DynamoDB execute_statement API call
    """
    # Step 1: Replace "=" with "' : '" to format into key-value pairs
    formbody = formbody.replace("=", "' : '")

    # Step 2: Replace "&" with "', '" to separate attributes
    formbody = formbody.replace("&", "', '")

    # Step 3: Wrap the formatted attributes into a PartiQL INSERT statement
    # Target table name: 'riteclicktable'
    formbody = "INSERT INTO riteclicktable value {'" + formbody + "'}"

    # Step 4: Initialize the Amazon DynamoDB client using boto3 (AWS SDK)
    client = boto3.client('dynamodb')

    # Step 5: Execute the PartiQL statement against Amazon DynamoDB
    response = client.execute_statement(Statement=formbody)

    # Assuming the execute_statement call returns successfully
    return response