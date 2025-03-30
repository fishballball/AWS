import socket
import boto3
import json
from datetime import datetime

def test_tcp_connection(domain, port=443, timeout=3):
    """
    Test TCP connectivity to a domain on the specified port.
    Returns a dictionary with connection details.
    """
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Start timer
        start_time = datetime.now()
        
        # Attempt to connect
        result = sock.connect_ex((domain, port))
        
        # Calculate connection time
        connection_time = (datetime.now() - start_time).total_seconds() * 1000  # in milliseconds
        
        # Close socket
        sock.close()
        
        # Check if connection was successful
        if result == 0:
            return {
                "success": True,
                "port": port,
                "latency_ms": round(connection_time, 2),
                "message": "Connection successful"
            }
        else:
            return {
                "success": False,
                "port": port,
                "error_code": result,
                "message": f"Connection failed with error code {result}"
            }
    
    except Exception as e:
        return {
            "success": False,
            "port": port,
            "error": str(e),
            "message": f"Exception during connection attempt: {str(e)}"
        }

def parse_domain_input(domain_input):
    """
    Parse domain input in format "domain:port"
    Returns (domain, port) tuple where port is an integer
    If no port is specified, returns default port 443
    """
    if ":" in domain_input:
        parts = domain_input.split(":", 1)
        domain = parts[0]
        try:
            port = int(parts[1])
            return domain, port
        except ValueError:
            # If port is not a valid integer, use default
            return domain_input, 443
    else:
        return domain_input, 443

def lambda_handler(event, context):
    # Get domains from event or use default
    domain_inputs = event.get('domains', ['example.com'])
    
    # Default port is only used if neither domain:port format nor domain_configs are used
    default_port = event.get('port', 443)
    
    # Allow domain-specific port configuration (for backward compatibility)
    domain_configs = event.get('domain_configs', {})
    
    results = []
    errors = []
    
    # Process each domain input
    for domain_input in domain_inputs:
        # Parse domain input to extract domain and port
        domain, port_from_input = parse_domain_input(domain_input)
        
        domain_result = {"domain": domain, "timestamp": datetime.now().isoformat()}
        
        try:
            # Resolve IP address for domain
            ip_address = socket.gethostbyname(domain)
            domain_result["ip_address"] = ip_address
            
            # Priority for port selection:
            # 1. Domain:port format in input
            # 2. Domain-specific config in domain_configs
            # 3. Default port from event
            if port_from_input != 443:  # If port was explicitly specified in domain:port format
                port = port_from_input
            else:
                port = domain_configs.get(domain, {}).get('port', default_port)
            
            # Perform TCP connection test
            conn_test = test_tcp_connection(domain, port=port)
            domain_result["tcp_test"] = conn_test
            
            # Add result
            results.append(domain_result)
            
        except Exception as e:
            errors.append({
                "domain": domain,
                "error": str(e)
            })
    
    # Prepare response data
    response_data = {
        "results": results,
        "errors": errors,
        "timestamp": datetime.now().isoformat()
    }
    
    # Convert to JSON
    result_json = json.dumps(response_data, indent=2)
    
    # Save to S3
    try:
        s3_client = boto3.client('s3')
        bucket_name = 'YOUR_S3_BUCKET_NAME'  # Replace with your actual bucket name
        
        # Use timestamp for unique filename
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        file_name = f'domain-connectivity-{timestamp}.json'
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=result_json,
            ContentType='application/json'
        )
        
        return {
            'statusCode': 200,
            'body': f'Successfully tested {len(results)} domains and saved to S3',
            'results': results,
            'errors': errors
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error saving to S3: {str(e)}',
            'results': results,
            'errors': errors
        } 