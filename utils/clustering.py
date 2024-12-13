import requests
import time
def send_cluster_request(retries=3 , delay=1):
    
    for attempt in range(1, retries+1):
        try:
            response = requests.post("http://127.0.0.1:8000/cluster-articles/")
            
            if(response.status_code == 200):
                print("Sent cluster request : " , response.status_code)
                return response.text
            else:
                print(f"Attempt {attempt}: Failed to send cluster request - Status code {response.status_code}")
                if(attempt < retries):
                    time.sleep(delay)
                else:
                    print(f"Attempt {attempt}: Failed to send cluster request - Status code {response.status_code}")
                    raise Exception(f"HTTP Error while sending cluster request: {response.status_code}")
            
        except Exception as e:
            raise Exception("Failed to send cluster request")