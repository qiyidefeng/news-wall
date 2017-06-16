import asyncio
import aiohttp
import json
import sqlite3
import datetime
from bs4 import BeautifulSoup


async def run(loop, url):
    try:
        async with aiohttp.ClientSession(loop=loop) as session:
            with aiohttp.Timeout(20, loop=session.loop):
                async with session.get(url) as response:
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
    elif(url=='theregister'):
        theregister(data)
    elif(url=='securityaffairs'):
        securityaffairs(data)

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
    #loop.run_until_complete(asyncio.gather(*[run(loop, 'http://securityaffairs.co/wordpress/')]))
    loop.run_until_complete(asyncio.gather(*[run(loop, 'http://securityaffairs.co/wordpress/'), run(loop, 'http://www.theregister.co.uk/security/'), run(loop, 'http://hackernews.cc/'), run(loop, 'http://www.freebuf.com'), run_easyaq(loop, 'https://www.easyaq.com/infoList')]))
    closedb(db, cu)

