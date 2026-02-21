import asyncio
import aiohttp
import requests
import time
import random
from telebot.async_telebot import AsyncTeleBot

bot = AsyncTeleBot('8016414905:AAGHGy2imdTzevs5A8297Kw6snpXZvUzQyU')
CHAT_IDS = [
    {'chat_id': '-1003795730228', 'thread_id': 2}
]
checked_proxies = set()
semaphore = asyncio.Semaphore(100)
proxy_counter = 0

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
    
    test_urls = [
        'http://httpbin.org/ip',
        'http://ip-api.com/json',
        'http://api.ipify.org?format=json',
        'http://checkip.amazonaws.com'
    ]
    test_url = random.choice(test_urls)
    
    proxy_str = None
    if proxy_type in ['HTTP', 'HTTPS']:
        proxy_str = f"{proxy_type.lower()}://{ip}:{port}"
    elif proxy_type == 'SOCKS5':
        proxy_str = f"socks5://{ip}:{port}"
    elif proxy_type == 'SOCKS4':
        proxy_str = f"socks4://{ip}:{port}"

    start_time = time.time()
    try:
        timeout = aiohttp.ClientTimeout(total=3)
        connector = aiohttp.TCPConnector(limit=100, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.get(test_url, proxy=proxy_str, ssl=False) as response:
                if response.status == 200:
                    await response.read()
                    ping = int((time.time() - start_time) * 1000)
                    if 20 <= ping <= 200:
                        checked_proxies.add(proxy_key)
                        return ping
    except:
        pass
    return None

async def safe_process_proxy(ip, port, proxy_type):
    async with semaphore:
        try:
            ping = await check_proxy(ip, port, proxy_type)
            if ping:
                country = get_country_from_ip(ip)
                flag = get_country_flag(country)
                global proxy_counter
                proxy_counter += 1
                
                message = f"""<b>Тип соединения</b>: <code>{proxy_type}</code>
<b>Местоположение сервера</b>: <code>{flag}</code>
<b>Время ответа сервера</b>: <code>{ping}ms</code>
<b>IP</b>: <code>{ip}</code>
<b>PORT</b>: <code>{port}</code>"""
                
                for chat in CHAT_IDS:
                    try:
                        await bot.send_message(chat['chat_id'], message, parse_mode='HTML', message_thread_id=chat['thread_id'])
                        await asyncio.sleep(0.05)
                    except Exception as e:
                        print(f"Ошибка отправки в чат {chat['chat_id']}: {e}")
                
                print(f"Найден прокси #{proxy_counter}: {ip}:{port} ({proxy_type}) - {ping}ms")
                await asyncio.sleep(0.1)
        except Exception as e:
            pass

async def parse_source(url, source_type):
    proxies = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, timeout=15, headers=headers)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if ':' in line and not line.startswith('#') and not line.startswith('//'):
                    parts = line.replace('://', ':').split(':')
                    if len(parts) >= 2:
                        ip = parts[0].strip()
                        port_part = parts[1].strip()
                        port = port_part.split()[0].strip() if ' ' in port_part else port_part
                        
                        proxy_type = 'HTTP'
                        if 'socks5' in source_type.lower() or 'socks5' in url.lower():
                            proxy_type = 'SOCKS5'
                        elif 'socks4' in source_type.lower() or 'socks4' in url.lower():
                            proxy_type = 'SOCKS4'
                        elif 'https' in source_type.lower() or 'https' in url.lower():
                            proxy_type = 'HTTPS'
                        
                        if port.isdigit() and 1 <= int(port) <= 65535:
                            proxies.append((ip, port, proxy_type))
    except Exception as e:
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
        ('https://www.proxy-list.download/api/v1/get?type=socks5', 'proxy-list_socks5'),
        ('https://raw.githubusercontent.com/almroot/proxylist/master/list.txt', 'almroot'),
        ('https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/main/proxies.txt', 'proxyscraper'),
        ('https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/http/global/http_checked.txt', 'yakumo_http'),
        ('https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/socks4/global/socks4_checked.txt', 'yakumo_socks4'),
        ('https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/socks5/global/socks5_checked.txt', 'yakumo_socks5'),
        ('https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt', 'proxy4parsing_http'),
        ('https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/socks5.txt', 'proxy4parsing_socks5'),
        ('https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt', 'mmpx12_http'),
        ('https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt', 'mmpx12_socks5'),
        ('https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt', 'rdavydov_http'),
        ('https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt', 'rdavydov_socks5'),
        ('https://raw.githubusercontent.com/saisuiu/uiu/main/free.txt', 'saisuiu'),
        ('https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/http_proxies.txt', 'anonym0uswork_http'),
        ('https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/https_proxies.txt', 'anonym0uswork_https'),
        ('https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/socks4_proxies.txt', 'anonym0uswork_socks4'),
        ('https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/socks5_proxies.txt', 'anonym0uswork_socks5'),
    ]
    
    cycle_count = 0
    
    while True:
        try:
            cycle_count += 1
            print(f"\n=== Цикл #{cycle_count} ===")
            
            all_proxies = []
            
            for url, source_type in sources:
                try:
                    proxies = await parse_source(url, source_type)
                    if proxies:
                        all_proxies.extend(proxies)
                        print(f"✓ {source_type}: {len(proxies)} прокси")
                    await asyncio.sleep(random.uniform(0.1, 0.5))
                except:
                    continue
            
            if not all_proxies:
                print("❌ Не удалось получить прокси ни из одного источника")
                await asyncio.sleep(30)
                continue
            
            unique_proxies = list(set(all_proxies))
            random.shuffle(unique_proxies)
            
            print(f"📊 Всего уникальных прокси: {len(unique_proxies)}")
            print(f"🔍 Начинаю проверку прокси...")
            
            batch_size = 200
            found_in_cycle = 0
            
            for i in range(0, len(unique_proxies), batch_size):
                batch = unique_proxies[i:i + batch_size]
                tasks = [safe_process_proxy(ip, port, proxy_type) for ip, port, proxy_type in batch]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if result and not isinstance(result, Exception):
                        found_in_cycle += 1
                
                processed = min(i + batch_size, len(unique_proxies))
                print(f"📈 Обработано: {processed}/{len(unique_proxies)} | Найдено рабочих: {found_in_cycle}")
                
                await asyncio.sleep(1)
            
            print(f"✅ Цикл завершен. Найдено рабочих прокси: {found_in_cycle}")
            print(f"⏳ Ожидание 10 секунд перед следующим циклом...")
            
            checked_proxies.clear()
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"⚠️ Ошибка в главном цикле: {e}")
            await asyncio.sleep(5)

async def main():
    print("🚀 Прокси-бот запущен!")
    print(f"📨 Отправка в {len(CHAT_IDS)} чата(ов)")
    print("=" * 50)
    
    try:
        await parse_and_check_proxies()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        print("🔄 Перезапуск через 10 секунд...")
        await asyncio.sleep(10)
        await main()

if __name__ == '__main__':
    asyncio.run(main())
