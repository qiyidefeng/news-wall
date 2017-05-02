import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup


async def fetch(session, url):
    with aiohttp.Timeout(20, loop=session.loop):
        async with session.get(url) as response:
            return await response.text()

async def run(loop, url):
    async with aiohttp.ClientSession(loop=loop) as session:
        data = await fetch(session, url)
        parse(url,data)

async def run_easyaq(loop, url):
    async with aiohttp.ClientSession(loop=loop) as session:
        with aiohttp.Timeout(20, loop=session.loop):
            async with session.post(url, data={'currentPage':'1','infotypeid':'0'}) as response:
                data = await response.text()
                parse(url,data)

def save(date, url, title):
    result.write('<div><a href="' + url + '">' + date + '  ' + title + '</a></div>\n')



def freebuf(data):
    soap = BeautifulSoup(data, 'html.parser')
    tags = soap.select('.news-info')
    for tag in tags:
        dl = tag.dl
        save(dl.dd.select('.time')[0].string.strip(), dl.dt.a['href'], dl.dt.a['title'])
        #result.write('<div><a href="' + dl.dt.a['href'] + '">' + dl.dd.select('.time')[0].string.strip() + '  ' + dl.dt.a['title'] + '</a></div>\n')

def easyaq(data):
   jn = json.loads(data)
   if(jn['retCode'] == 1):
       for item in jn['retObj']:
           save(item['info']['releasetime'], 'https://www.easyaq.com/news/' + str(item['info']['id']) + '.shtml', item['info']['name'])
           #result.write('<div><a href="https://www.easyaq.com/news/' + str(item['info']['id']) + '.shtml">' + item['info']['releasetime'] + '  ' + item['info']['name'] + '</a></div>\n')

def hackernews(data):
    soap = BeautifulSoup(data, 'html.parser')
    tags = soap.select('.classic-list-right')
    for tag in tags:
        save(tag.select('span')[1].a.string, tag.h3.a['href'], tag.h3.a.string)
        #result.write('<div><a href="' + tag.h3.a['href'] + '">' + tag.select('span')[1].a.string + '  ' + tag.h3.a.string + '</a></div>\n')
    

def parse(url, data):
    if(url.startswith('https')):
        url = url[8:]
    else:
        url = url[7:]
    words = url.split('.')
    if(words[0]=='www'):
        url = words[1]
    else:
        url = words[0]

    if(url=='freebuf'):
        freebuf(data)
    elif(url=='easyaq'):
        easyaq(data)
    elif(url=='hackernews'):
        hackernews(data)

if __name__=='__main__':
    loop = asyncio.get_event_loop()
    result = open('result.html', 'w')
    last = open('last.txt', 'w')
    result.write('<html lang="en">\n<head>\n<meta charset="UTF-8">\n<title>news-wall</title>\n</head>\n<body>\n')
    loop.run_until_complete(asyncio.gather(*[run(loop, 'http://hackernews.cc/'), run(loop, 'http://www.freebuf.com'), run_easyaq(loop, 'https://www.easyaq.com/infoList')]))
    result.write('</body>\n</html>\n')
    result.close()
    last.close()

