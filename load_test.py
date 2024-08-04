import aiohttp
import asyncio
import time
import json
import argparse
from collections import Counter

async def fetch(session, method, url, data=None):
    start_time = time.time()
    async with session.request(method, url, json=data) as response:
        end_time = time.time()
        response_time = end_time - start_time
        status_family = f"{response.status // 100}XX"
        return response_time, status_family

async def bound_fetch(sem, session, method, url, data=None):
    async with sem:
        return await fetch(session, method, url, data)

async def run(method, url, file_name, num_users, total_requests):
    tasks = []
    sem = asyncio.Semaphore(num_users)

    async with aiohttp.ClientSession() as session:
        if method != 'GET' and file_name:
            with open(file_name, 'r') as f:
                data = json.load(f)
        else:
            data = None

        for _ in range(total_requests):
            task = asyncio.ensure_future(bound_fetch(sem, session, method, url, data))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

    return responses

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('method', type=str, help='HTTP method to use (GET, POST, etc.)')
    parser.add_argument('url', type=str, help='URL to request')
    parser.add_argument('num_users', type=int, help='Number of concurrent users')
    parser.add_argument('total_requests', type=int, help='Total number of requests')
    parser.add_argument('file_name', type=str, nargs='?', default=None, help='File name for request body (optional for non-GET requests)')

    args = parser.parse_args()

    method = args.method.upper()
    url = args.url
    file_name = args.file_name
    num_users = args.num_users
    total_requests = args.total_requests

    start_time = time.time()
    responses = asyncio.run(run(method, url, file_name, num_users, total_requests))
    end_time = time.time()

    total_time = end_time - start_time
    total_requests_made = len(responses)
    avg_rps = total_requests_made / total_time
    max_time = max([r[0] for r in responses])
    min_time = min([r[0] for r in responses])
    avg_time = sum([r[0] for r in responses]) / total_requests_made

    status_counts = Counter([r[1] for r in responses])
    total_responses = sum(status_counts.values())
    status_percentages = {status: (count / total_responses) * 100 for status, count in status_counts.items()}

    print(f"=====================")
    print(f"Total requests: {total_requests_made}")
    print(f"Average requests per second: {avg_rps:.2f}")
    print(f"Total time for requests: {total_time:.2f} seconds")
    print(f"Max response time: {max_time:.2f} seconds")
    print(f"Min response time: {min_time:.2f} seconds")
    print(f"Average response time: {avg_time:.2f} seconds")
    print(f"=====================")
    print("HTTP status code percentages:")
    for status, percentage in status_percentages.items():
        print(f"{status}: {percentage:.2f}%")
    print(f"=====================")


if __name__ == '__main__':
    main()
