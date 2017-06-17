import asyncio
import aiohttp
import json
import sqlite3
import datetime
from bs4 import BeautifulSoup

headers={
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/9.0.601.0 Safari/534.14',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.8',
}


async def run(loop, url):
    try:
        async with aiohttp.ClientSession(loop=loop) as session:
            with aiohttp.Timeout(20, loop=session.loop):
                async with session.get(url, headers=headers) as response:
                    data = await response.text()
                    parse(url,data)
    except Exception as e:
        print('Failed!',url)

async def run_easyaq(loop, url):
    try:
        async with aiohttp.ClientSession(loop=loop) as session:
            with aiohttp.Timeout(20, loop=session.loop):
                async with session.post(url, data={'currentPage':'1','infotypeid':'0'}) as response:
                    data = await response.text()
                    parse(url,data)
    except Exception as e:
        print('Failed!',url)

def save(src, date, url, title):
    try:
        insert_stmt = 'insert into news values(?,?,?,?,?)'
        cu.execute(insert_stmt, (url, title, src, date, start_time))
    except sqlite3.IntegrityError as e:
        #print('dumplicated!')
        pass

def trendmicro(data):
    soap = BeautifulSoup(data, 'html.parser')
    tags = soap.select('.post')
    for tag in tags:
        title = tag.div.div.a.h1.string
        url = tag.div.div.a['href']
        date = tag.select('.post-date')[0].div.a.string
        save('trendmicro', date, url, title)


def threatpost(data):
    soap = BeautifulSoup(data, 'html.parser')
    tags = soap.select('#latest-posts article')
    for tag in tags:
        title = tag.h3.a['title']
        url = tag.h3.a['href']
        date = tag.select('time')[0].string
        save('threatpost', date, url, title)
    


def freebuf(data):
    soap = BeautifulSoup(data, 'html.parser')
    tags = soap.select('.news-info')
    for tag in tags:
        dl = tag.dl
        save('freebuf', dl.dd.select('.time')[0].string.strip(), dl.dt.a['href'], dl.dt.a['title'])

def easyaq(data):
   jn = json.loads(data)
   if(jn['retCode'] == 1):
       for item in jn['retObj']:
           save('easyaq', item['info']['releasetime'], 'https://www.easyaq.com/news/' + str(item['info']['id']) + '.shtml', item['info']['name'])

def hackernews(data):
    soap = BeautifulSoup(data, 'html.parser')
    tags = soap.select('.classic-list-right')
    for tag in tags:
        save('hackernews', tag.select('span')[1].a.string, tag.h3.a['href'], tag.h3.a.string)
    
def theregister(data):
    soap = BeautifulSoup(data, 'html.parser')
    tags = soap.select('.headlines')[0].select('.story_link')
    for tag in tags:
        save('theregister', tag.select('.time_stamp')[0].span.string, 'http://www.theregister.co.uk'+tag['href'], tag.h4.string)

def securityaffairs(data):
    soap = BeautifulSoup(data, 'html.parser')
    tags = soap.select('.post_inner_wrapper')
    for tag in tags:
        save('securityaffairs', tag.select('.post_detail')[0].a.string, tag.select('.post_header')[0].h3.a['href'], tag.select('.post_header')[0].h3.a['title'])

def parse(url, data):
    if('freebuf' in url):
        freebuf(data)
    elif('easyaq' in url):
        easyaq(data)
    elif('hackernews' in url):
        hackernews(data)
    elif('theregister' in url):
        theregister(data)
    elif('securityaffairs' in url):
        securityaffairs(data)
    elif('threatpost' in url):
        threatpost(data)
    elif('trendmicro' in url):
        trendmicro(data)

def initdb():
    db = sqlite3.connect('data.db')
    cu = db.cursor()
    cu.execute("create table if not exists news (url varchar(300) primary key, title varchar(100), source varchar(50), pubtime varchar(30), downtime varchar(30))")
    return db, cu


def closedb(db, cu):
    db.commit()
    cu.close()
    db.close()

if __name__=='__main__':
    db, cu = initdb()
    start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    loop = asyncio.get_event_loop()
    #loop.run_until_complete(asyncio.gather(*[run(loop, 'http://blog.trendmicro.com')]))
    url_list =['http://securityaffairs.co/wordpress/',
               'http://www.theregister.co.uk/security/',
               'http://hackernews.cc/',
               'http://www.freebuf.com',
               'https://threatpost.com/blog/',
               'http://blog.trendmicro.com']
    tasks = []
    for url in url_list:
        tasks.append(run(loop, url))
    tasks.append(run_easyaq(loop, 'https://www.easyaq.com/infoList'))
    loop.run_until_complete(asyncio.gather(*tasks))
    closedb(db, cu)

