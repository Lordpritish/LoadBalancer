import requests
from multiprocessing import Process
import time

def make_request(session):
    url = 'http://10.0.1.1'

    response = session.get(url)


for _ in range(100):
    session = requests.Session()
    make_request(session)
    # p = Process(target=make_request, args=(session,))
    # p.start()
    # p.join()
    # time.sleep(1)