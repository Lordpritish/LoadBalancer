import requests
import time

# Function to send a request to the load balancer
def send_request(load_balancer_ip):
    url = 'http://{}'.format(load_balancer_ip)
    try:
        response = requests.get(url)
        print 'Response from server:', response.text
    except requests.RequestException as e:
        print 'Error:', e

# Main function to control the number of requests and delay
def main(load_balancer_ip, num_requests, delay):
    for _ in range(num_requests):
        send_request(load_balancer_ip)
        time.sleep(delay)

if __name__ == "__main__":
    load_balancer_ip = '10.0.1.1'  # Load balancer IP
    num_requests = 100  # Number of requests to send
    delay = 1  # Delay in seconds between requests
    main(load_balancer_ip, num_requests, delay)