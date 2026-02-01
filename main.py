import asyncio
import aiohttp
import requests
import time
from telebot.async_telebot import AsyncTeleBot

bot = AsyncTeleBot('8204956074:AAEcZLIbSO4pDdv4kgRZA7VSluXc5YHogWc')
CHAT_IDS = [
    {'chat_id': '-1003688643920', 'thread_id': 14},
    {'chat_id': '-1003579850616', 'thread_id': 35}
]
checked_proxies = set()
semaphore = asyncio.Semaphore(50)

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
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=countryCode', timeout=2)
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

    test_url = 'http://httpbin.org/ip'
    
    proxy_str = None
    if proxy_type in ['HTTP', 'HTTPS']:
        proxy_str = f"{proxy_type.lower()}://{ip}:{port}"
    elif proxy_type == 'SOCKS5':
        proxy_str = f"socks5://{ip}:{port}"
    elif proxy_type == 'SOCKS4':
        proxy_str = f"socks4://{ip}:{port}"

    start_time = time.time()
    try:
        timeout = aiohttp.ClientTimeout(total=2)
        connector = aiohttp.TCPConnector(limit=10)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.get(test_url, proxy=proxy_str) as response:
                if response.status == 200:
                    ping = int((time.time() - start_time) * 1000)
                    if 20 <= ping <= 200:
                        return ping
    except Exception as e:
        if "10054" not in str(e) and "10053" not in str(e):
            pass
    return None

async def safe_process_proxy(ip, port, proxy_type):
    async with semaphore:
        try:
            ping = await check_proxy(ip, port, proxy_type)
            if ping:
                country = get_country_from_ip(ip)
                flag = get_country_flag(country)
                message = f"""<b>Тип соединения</b>: <code>{proxy_type}</code>
<b>Местоположение сервера</b>: <code>{flag}</code>
<b>Время ответа сервера</b>: <code>{ping}ms</code>
<b>IP</b>: <code>{ip}</code>
<b>PORT</b>: <code>{port}</code>"""
                for chat in CHAT_IDS:
                    try:
                        await bot.send_message(chat['chat_id'], message, parse_mode='HTML', message_thread_id=chat['thread_id'])
                        await asyncio.sleep(0.1)
                    except:
                        pass
                await asyncio.sleep(0.2)
        except:
            pass

async def parse_source(url, source_type):
    proxies = []
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        ip = parts[0].strip()
                        port = parts[1].split()[0].strip() if ' ' in parts[1] else parts[1].strip()
                        
                        proxy_type = 'HTTP'
                        if 'socks5' in source_type.lower() or 'socks5' in url.lower():
                            proxy_type = 'SOCKS5'
                        elif 'socks4' in source_type.lower() or 'socks4' in url.lower():
                            proxy_type = 'SOCKS4'
                        elif 'https' in source_type.lower() or 'https' in url.lower():
                            proxy_type = 'HTTPS'
                        
                        if port.isdigit() and 1 <= int(port) <= 65535 and ip.replace('.', '').isdigit():
                            proxies.append((ip, port, proxy_type))
    except:
        pass
    return proxies

async def parse_and_check_proxies():
    sources = [
        ('https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all', 'proxyscrape_http'),
        ('https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all', 'proxyscrape_socks4'),
        ('https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all', 'proxyscrape_socks5'),
        ('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt', 'github_http'),
        ('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt', 'github_socks5'),
        ('https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt', 'shifty_http'),
        ('https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt', 'shifty_https'),
        ('https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt', 'hookzof_socks5'),
        ('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt', 'jetkai_http'),
        ('https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt', 'jetkai_https'),
        ('https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt', 'monosans_http'),
        ('https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt', 'monosans_socks5'),
        ('https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt', 'roosterkid_http'),
        ('https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt', 'roosterkid_https'),
        ('https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt', 'roosterkid_socks5'),
        ('https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/http.txt', 'saschazesiger_http'),
        ('https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/https.txt', 'saschazesiger_https'),
        ('https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt', 'saschazesiger_socks5'),
        ('https://www.proxy-list.download/api/v1/get?type=http', 'proxy-list_http'),
        ('https://www.proxy-list.download/api/v1/get?type=https', 'proxy-list_https'),
        ('https://www.proxy-list.download/api/v1/get?type=socks4', 'proxy-list_socks4'),
        ('https://www.proxy-list.download/api/v1.get?type=socks5', 'proxy-list_socks5'),
    ]
    
    while True:
        try:
            all_proxies = []
            print("Начинаю парсинг источников...")
            
            for url, source_type in sources:
                try:
                    proxies = await parse_source(url, source_type)
                    all_proxies.extend(proxies)
                    print(f"Источник {source_type}: найдено {len(proxies)} прокси")
                    await asyncio.sleep(0.5)
                except:
                    continue
            
            unique_proxies = list(set(all_proxies))
            print(f"Всего уникальных прокси для проверки: {len(unique_proxies)}")
            
            batch_size = 100
            for i in range(0, len(unique_proxies), batch_size):
                batch = unique_proxies[i:i + batch_size]
                tasks = [safe_process_proxy(ip, port, proxy_type) for ip, port, proxy_type in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
                print(f"Обработано {min(i + batch_size, len(unique_proxies))}/{len(unique_proxies)} прокси")
                await asyncio.sleep(1)
            
            print(f"Цикл завершен. Ожидание 30 секунд...")
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Ошибка в главном цикле: {e}")
            await asyncio.sleep(10)

async def main():
    try:
        await parse_and_check_proxies()
    except KeyboardInterrupt:
        print("Бот остановлен")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        await asyncio.sleep(5)
        await main()

if __name__ == '__main__':
    asyncio.run(main())
