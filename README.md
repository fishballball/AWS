# AWS Lambda IP Resolver & Connectivity Tester

This Lambda function resolves the IP addresses of multiple domains, performs TCP connectivity tests on specified ports, and saves the results to an S3 bucket.

## Deployment Instructions

1. Create an S3 bucket or use an existing one
2. Update the `bucket_name` variable in `lambda_function.py` with your actual S3 bucket name
3. Create a deployment package:
   ```bash
   pip install -r requirements.txt -t ./package
   cp lambda_function.py ./package/
   cd package
   zip -r ../deployment-package.zip .
   cd ..
   ```
4. Create a Lambda function in the AWS Console:
   - Runtime: Python 3.9 or newer
   - Upload the deployment-package.zip file
   - Set the handler to `lambda_function.lambda_handler`
   - Set an appropriate timeout (at least 10 seconds) since connectivity testing requires more time
5. Configure IAM permissions:
   - Ensure the Lambda execution role has permissions to write to the S3 bucket
   - Example policy:
     ```json
     {
         "Version": "2012-10-17",
         "Statement": [
             {
                 "Effect": "Allow",
                 "Action": [
                     "s3:PutObject"
                 ],
                 "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*"
             }
         ]
     }
     ```
6. Test the Lambda function using the AWS console

## Invoking the Function

You can invoke the Lambda function with a list of domains to resolve using multiple formats:

### Basic Usage

```json
{
  "domains": [
    "example.com",
    "google.com",
    "amazon.com"
  ]
}
```

### Domain:Port Format (Recommended)

You can specify the port directly in the domain string using the format `domain:port`:

```json
{
  "domains": [
    "example.com:80",
    "google.com:443",
    "amazon.com:8080"
  ]
}
```

### Custom Port (Applied to All Domains)

You can specify a default port to test (instead of the default 443):

```json
{
  "domains": ["example.com", "google.com", "amazon.com"],
  "port": 80
}
```

### Domain-Specific Port Configuration

You can also specify different ports for specific domains:

```json
{
  "domains": ["example.com", "google.com", "amazon.com"],
  "port": 443,
  "domain_configs": {
    "example.com": {
      "port": 80
    },
    "google.com": {
      "port": 8443
    }
  }
}
```

### Port Selection Priority

When multiple port specifications are present, the function uses the following priority:
1. Port specified in the domain:port format (e.g., "example.com:8080")
2. Port specified in domain_configs for the specific domain
3. Default port specified in the "port" parameter
4. 443 (HTTPS) if no port is specified anywhere

## Output Format

The function saves a JSON file to S3 with the following structure:

```json
{
  "results": [
    {
      "domain": "example.com",
      "timestamp": "2023-07-25T15:30:45.123456",
      "ip_address": "93.184.216.34",
      "tcp_test": {
        "success": true,
        "port": 80,
        "latency_ms": 125.34,
        "message": "Connection successful"
      }
    },
    {
      "domain": "google.com",
      "timestamp": "2023-07-25T15:30:45.234567",
      "ip_address": "142.250.185.78",
      "tcp_test": {
        "success": true,
        "port": 443,
        "latency_ms": 78.12,
        "message": "Connection successful"
      }
    }
  ],
  "errors": [
    {
      "domain": "invalid-domain.xyz",
      "error": "socket.gaierror: [Errno 11001] getaddrinfo failed"
    }
  ],
  "timestamp": "2023-07-25T15:30:45.345678"
}
```

## TCP Connectivity Test

The function performs a TCP connectivity test on the specified port for each domain with these steps:
1. Creates a socket connection to the domain on the specified port (default: 443 for HTTPS)
2. Measures the connection latency in milliseconds
3. Reports success or failure with error details

The TCP test results include:
- `success`: Boolean indicating if the connection was successful
- `port`: The port that was tested
- `latency_ms`: Connection time in milliseconds (for successful connections)
- `error_code` or `error`: Details about the failure (for failed connections)
- `message`: Human-readable description of the result

## Scheduling Regular Execution

To run this Lambda function on a schedule:

1. Go to Amazon EventBridge (CloudWatch Events)
2. Create a new rule
3. Use a schedule expression (e.g., `rate(1 hour)` for hourly execution)
4. Select your Lambda function as the target
5. Optionally, provide a constant JSON input with your list of domains and port configurations
6. Save the rule 