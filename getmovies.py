from requests import request
import aiohttp
import asyncio
import logging


async def get_new_releases_per_country(queue,country):
    
    url = "https://unogs-unogs-v1.p.rapidapi.com/aaapi.cgi"
    querystring = {"q":f"get:new7:{country}","p":"1","t":"ns","st":"adv"}
    headers = {
        'x-rapidapi-host': "unogs-unogs-v1.p.rapidapi.com",
        'x-rapidapi-key': "9f962eca91mshba30e867095f649p1c0727jsnd3e8f404a0b3"
    }
    async with aiohttp.request("GET", url, headers=headers, params=querystring) as resp:
        assert resp.status == 200
        results = await resp.json()
        queue.put_nowait(results)

async def handle_results(queue):
    results = await queue.get()
    print('results from 1st query:\n')
    print_movie_names(results)
    results2 = await queue.get()
    print('results from 2nd query:\n')
    print_movie_names(results2)
    print('union query:\n')
    print([item for item in results if item in results2])

async def async_run():
    queue = asyncio.Queue()
    asyncio.create_task(get_new_releases_per_country(queue,"ZA"))
    asyncio.create_task(get_new_releases_per_country(queue,"IT"))
    handler = asyncio.create_task(handle_results(queue))
    await handler

def print_movie_names(results):
    for item in results['ITEMS']: 
        print(item['title']) 


if __name__ == '__main__':
    asyncio.run(async_run())