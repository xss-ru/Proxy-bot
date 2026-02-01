import asyncio
import aiohttp
import requests
import time
from telebot.async_telebot import AsyncTeleBot

bot = AsyncTeleBot('8204956074:AAEcZLIbSO4pDdv4kgRZA7VSluXc5YHogWc')
CHAT_ID = '-1003688643920'
THREAD_ID = 14
checked_proxies = set()

def get_country_flag(country_code):
    flag_map = {
        'US': '🇺🇸', 'RU': '🇷🇺', 'DE': '🇩🇪', 'FR': '🇫🇷', 'JP': '🇯🇵',
        'GB': '🇬🇧', 'CN': '🇨🇳', 'BR': '🇧🇷', 'IN': '🇮🇳', 'CA': '🇨🇦',
        'AU': '🇦🇺', 'IT': '🇮🇹', 'ES': '🇪🇸', 'NL': '🇳🇱', 'SE': '🇸🇪',
        'PL': '🇵🇱', 'UA': '🇺🇦', 'TR': '🇹🇷', 'KR': '🇰🇷', 'SG': '🇸🇬'
    }
    return flag_map.get(country_code.upper(), '🏴')

def get_country_from_ip(ip):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=countryCode', timeout=3)
        if response.status_code == 200:
            data = response.json()
            return data.get('countryCode', 'UN')
    except:
        pass
    return 'UN'

async def check_proxy(ip, port, proxy_type):
    proxy_key = f"{ip}:{port}:{proxy_type}"
    if proxy_key in checked_proxies:
        return None
    checked_proxies.add(proxy_key)

    test_urls = {
        'HTTP': 'http://httpbin.org/ip',
        'HTTPS': 'https://httpbin.org/ip',
        'SOCKS5': 'https://httpbin.org/ip'
    }
    url = test_urls.get(proxy_type, 'http://httpbin.org/ip')
    
    proxy_str = None
    if proxy_type in ['HTTP', 'HTTPS']:
        proxy_str = f"{proxy_type.lower()}://{ip}:{port}"
    elif proxy_type == 'SOCKS5':
        proxy_str = f"socks5://{ip}:{port}"

    start_time = time.time()
    try:
        timeout = aiohttp.ClientTimeout(total=3)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, proxy=proxy_str) as response:
                if response.status == 200:
                    ping = int((time.time() - start_time) * 1000)
                    if 20 <= ping <= 200:
                        return ping
    except:
        pass
    return None

async def process_proxy(ip, port, proxy_type):
    ping = await check_proxy(ip, port, proxy_type)
    if ping:
        country = get_country_from_ip(ip)
        flag = get_country_flag(country)
        message = f"""<b>Тип соединения</b>: <code>{proxy_type}</code>
<b>Местоположение сервера</b>: <code>{flag}</code>
<b>Время ответа сервера</b>: <code>{ping}ms</code>
<b>IP</b>: <code>{ip}</code>
<b>PORT</b>: <code>{port}</code>"""
        try:
            await bot.send_message(CHAT_ID, message, parse_mode='HTML', message_thread_id=THREAD_ID)
            await asyncio.sleep(0.5)
        except:
            pass

async def parse_and_check_proxies():
    sources = [
        ('https://free-proxy-list.net/', 'free_proxy_list'),
        ('https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all', 'proxyscrape'),
        ('https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc', 'geonode'),
        ('https://www.proxyspace.pro/api/v1/proxy/list?country=all&protocol=http,https,socks5&limit=100', 'proxyspace'),
        ('https://openproxy.space/list/http', 'openproxy'),
        ('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt', 'github_http'),
        ('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt', 'github_socks5'),
        ('https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt', 'shifty_http'),
        ('https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt', 'shifty_https'),
        ('https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt', 'hookzof'),
        ('https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt', 'proxifly_http'),
        ('https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt', 'proxifly_socks5'),
        ('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt', 'jetkai_http'),
        ('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt', 'jetkai_https'),
        ('https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt', 'mertguvencli'),
        ('https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt', 'sunny9577'),
        ('https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt', 'roosterkid_https'),
        ('https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt', 'roosterkid_socks5'),
        ('https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt', 'roosterkid_socks4'),
        ('https://api.openproxylist.xyz/http.txt', 'openproxylist_http'),
        ('https://api.openproxylist.xyz/socks4.txt', 'openproxylist_socks4'),
        ('https://api.openproxylist.xyz/socks5.txt', 'openproxylist_socks5'),
        ('https://www.proxy-list.download/api/v1/get?type=http', 'proxy-list_http'),
        ('https://www.proxy-list.download/api/v1/get?type=https', 'proxy-list_https'),
        ('https://www.proxy-list.download/api/v1/get?type=socks4', 'proxy-list_socks4'),
        ('https://www.proxy-list.download/api/v1/get?type=socks5', 'proxy-list_socks5'),
        ('https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=text', 'proxyscrape_all'),
        ('https://multiproxy.org/txt_all/proxy.txt', 'multiproxy'),
        ('https://www.freeproxychecker.com/result/http_proxies.txt', 'freeproxychecker_http'),
        ('https://www.freeproxychecker.com/result/https_proxies.txt', 'freeproxychecker_https'),
    ]
    
    while True:
        tasks = []
        for url, source_type in sources:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if ':' in line:
                            parts = line.split(':')
                            if len(parts) >= 2:
                                ip = parts[0].strip()
                                port = parts[1].strip()
                                
                                proxy_type = 'HTTP'
                                if 'socks5' in source_type or 'SOCKS5' in url:
                                    proxy_type = 'SOCKS5'
                                elif 'socks4' in source_type or 'SOCKS4' in url:
                                    proxy_type = 'SOCKS4'
                                elif 'https' in source_type or 'HTTPS' in url:
                                    proxy_type = 'HTTPS'
                                
                                if port.isdigit() and 1 <= int(port) <= 65535:
                                    tasks.append(process_proxy(ip, port, proxy_type))
            except:
                continue
        
        print(f"Найдено прокси для проверки: {len(tasks)}")
        
        batch_size = 100
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            await asyncio.gather(*batch, return_exceptions=True)
            await asyncio.sleep(1)
        
        await asyncio.sleep(30)

async def main():
    await asyncio.gather(
        parse_and_check_proxies(),
    )

if __name__ == '__main__':
    asyncio.run(main())
