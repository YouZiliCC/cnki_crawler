import time
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

options = webdriver.ChromeOptions()
# 1) 无头 + 窗口大小
options.add_argument('--headless=new')
options.add_argument('--window-size=1920,1080')
# 2) UA 与反检测
ua = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
      'AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/138.0.0.0 Safari/537.36')
options.add_argument(f'--user-agent={ua}')
options.add_argument('--disable-blink-features=AutomationControlled')
# 3) 资源禁用
prefs = {
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.stylesheet": 2,
}
options.add_experimental_option("prefs", prefs)
# 4) 系统级减负
options.add_argument('--disable-extensions')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--enable-unsafe-swiftshader')
# 5) 只创建一次 driver
driver = webdriver.Chrome(options=options)

def get_info():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT institution, url, result_count, page_count, crawled_or_not FROM infos;
    ''')
    infos = []
    for institution, url, result_count, page_count, crawled_or_not in cursor.fetchall():
        if crawled_or_not == 0:
            infos.append((institution, url, result_count, page_count))
        else:
            print(f"Skipping {institution}")            
    conn.close()
    return infos

def switch_to_50_per_page():
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@id='perPageDiv']//div"))
        )
        select1 = driver.find_element(By.XPATH, "//div[@id='perPageDiv']//div")
        select1.click()
        select2 = driver.find_element(By.XPATH, "//div[@id='perPageDiv']//li[@data-val='50']/a")
        select2.click()
        return True
    except Exception as e:
        print("Error switching to 50 per page:", e)
        return False

def set_crawled(institution):
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE infos SET crawled_or_not = 1 WHERE institution = ?;
        ''', (institution,))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error setting crawled:", e)

def page_extract_data(institution):
    # Extract data from the page
    count = 0
    # //td[@class='name']//a.text
    # //td[@class='author']/a[@class='KnowledgeNetLink']
    # //td[@class='source']/p.text
    # //td[@class='date'].text
    # //td[@class='data']/span.text
    # //td[@class='quote']/span.text
    # //td[@class='download']//a.text
    length = len(driver.find_elements(By.XPATH, "//tbody//tr"))
    for i in range(length):
        count += 1
        # name
        name = driver.find_element(By.XPATH, f"//tbody//tr[position()>0][{i+1}]//td[@class='name']//a").text
        # author
        authors1 = ';'.join(a.text for a in driver.find_elements(
            By.XPATH, f"//tbody//tr[position()>0][{i+1}]//td[@class='author']/a[@class='KnowledgeNetLink']"
        )) or 'None'
        authors2 = ';'.join([
            driver.execute_script("return arguments[0].textContent.trim();", a)
            for a in driver.find_elements(
                By.XPATH,
                f"//tbody//tr[position()>0][{i+1}]//td[@class='author']/span/a[@class='KnowledgeNetLink']"
                )
        ])
        authors = f"{authors1};{authors2}".strip(';').strip(',').strip('，').strip('、')
        if authors == '' or authors == ' ':
            authors = 'None'
        if authors == 'None':
            try:
                authors_links = driver.find_element(By.XPATH, f"//tbody//tr[position()>0][{i+1}]//td[@class='author']/a").text
                if ',' in authors_links:
                    authors = ';'.join(authors_links.split(',')).strip()
                elif '，' in authors_links:
                    authors = ';'.join(authors_links.split('，')).strip()
                elif '、' in authors_links:
                    authors = ';'.join(authors_links.split('、')).strip()
            except Exception as e:
                authors = 'None'
        if authors == 'None':
            try:
                # //tbody//tr[position()>0][4]//td[@class='author']//a[@style='pointer-events: none;']
                authors = ';'.join([
                driver.execute_script("return arguments[0].textContent.trim();", a)
                for a in driver.find_elements(
                    By.XPATH,
                    f"//tbody//tr[position()>0][{i+1}]//td[@class='author']//a[@style='pointer-events: none;']"
                    )
                ])
            except Exception as e:
                authors = 'None'
        if authors == '' or authors == ' ':
            authors = 'None'
        # source
        try:
            source = driver.find_element(By.XPATH, f"//tbody//tr[position()>0][{i+1}]//td[@class='source']//p").text
        except Exception as e:
            source = 'None'
        if source == '':
            source = 'None'
        if source == 'None':
            try:
                source = driver.find_element(By.XPATH, f"//tbody//tr[position()>0][{i+1}]//td[@class='source']/span").text
            except Exception as e:
                source = 'None'
        if source == 'None':
            try:
                source = driver.find_element(By.XPATH, f"//tbody//tr[position()>0][{i+1}]//a").text
            except Exception as e:
                source = 'None'
        # date
        try:
            date = driver.find_element(By.XPATH, f"//tbody//tr[position()>0][{i+1}]//td[@class='date']").text
        except Exception as e:
            date = 'None'
        # data
        try:
            data = driver.find_element(By.XPATH, f"//tbody//tr[position()>0][{i+1}]//td[@class='data']//span").text
        except Exception as e:
            data = 'None'
        # quote
        try:
            quote = driver.find_element(By.XPATH, f"//tbody//tr[position()>0][{i+1}]//td[@class='quote']//span").text
        except Exception as e:
            quote = '0'
        # download
        try:
            download = driver.find_element(By.XPATH, f"//tbody//tr[position()>0][{i+1}]//td[@class='download']//a").text
        except Exception as e:
            download = '0'
        # institution

        data = {
            'institution': institution,
            'name': name,
            'author': authors,
            'source': source,
            'date': date,
            'data': data,
            'quote': quote,
            'download': download,
        }
        save_data(data)

    return count

def show_ye():
    try:
        show = driver.find_elements(By.XPATH, "//dd[@field='YE']//a[@class='btn']")
        if not show:
            print("No year button found")
        else:
            show = show[0]
            show.click()
    except Exception as e:
        print("Error showing year:", e)

def click_ye():
    try:
        els = driver.find_elements(By.XPATH, "//dd[@field='YE']//li")
        if not els:
            YE = driver.find_element(By.XPATH, "//dt[@groupid='YE']//b")
            YE.click()
            return False
        else:
            return True
    except Exception as e:
        print("Error examining year:", e)
        return False

def crawl_data(institution, url, result_count, page_count):
    driver.get(url)
    time.sleep(2)
    driver.refresh()
    time.sleep(1)
    suc_ = switch_to_50_per_page()
    time.sleep(1)
    page_count = result_count // 20 + (1 if result_count % 20 > 0 else 0) if not suc_ else page_count
    time.sleep(0.5)
    count = 0

    for i in range(1, page_count + 1):
        count += page_extract_data(institution)
        print(f"{institution}:{i}/{page_count}-{count}/{result_count}")

        if i < page_count:
            try:
                next_page = driver.find_element(By.XPATH, "//a[@class='pagesnums']")
                driver.execute_script("arguments[0].click();", next_page)
            except Exception as e:
                print("Error clicking next page:", e)
            time.sleep(1)
    
    set_crawled(institution)

def crawl_data_divided(institution, url, result_count, page_count):
    # //dd[@field='YE']//li//input value text
    driver.get(url)
    time.sleep(2)
    driver.refresh()
    time.sleep(1)
    suc_ = switch_to_50_per_page()
    time.sleep(1)

    page_count = result_count // 20 + (1 if result_count % 20 > 0 else 0) if not suc_ else page_count

    time.sleep(0.5)
    count = 0
    click_ye()
    time.sleep(0.5)
    show_ye()

    length = len(driver.find_elements(By.XPATH, "//dd[@field='YE']//li"))
    for i in range(length):
        click_ye()
        time.sleep(0.5)
        show_ye()
        x = 10
        els = driver.find_elements(By.XPATH, "//dd[@field='YE']//li")
        clik = els[i + x].find_element(By.XPATH, ".//input")
        year = clik.get_attribute('value')
        year_count = els[i + x].find_element(By.XPATH, ".//span").text.strip('(').strip(')')
        clik.click()
        page_year_count = int(year_count) // 50 + (1 if int(year_count) % 50 > 0 else 0) if suc_ else int(year_count) // 20 + (1 if int(year_count) % 20 > 0 else 0)
        time.sleep(0.5)
        for i in range(1, page_year_count + 1):
            count += page_extract_data(institution)
            print(f"{institution}{year}:{i}/{page_year_count}-{count}/{result_count}")

            if i < page_year_count:
                try:
                    next_page = driver.find_element(By.XPATH, "//a[@class='pagesnums']")
                    driver.execute_script("arguments[0].click();", next_page)
                except Exception as e:
                    print("Error clicking next page:", e)
                time.sleep(1)
        click_ye()
        clik = driver.find_element(By.XPATH, "//dd[@field='YE']//li//input")
        clik.click()
        time.sleep(1.5)
        
    set_crawled(institution)


def save_data(data):
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                institution TEXT,
                name TEXT NOT NULL,
                author TEXT,
                source TEXT,
                date TEXT,
                data TEXT,
                quote TEXT,
                download TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, author, source, date, data, quote, download)
            );
        ''')
        cursor.execute("INSERT OR IGNORE INTO papers (institution, name, author, source, date, data, quote, download) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (data['institution'],
                    data['name'],
                    data['author'],
                    data['source'],
                    data['date'],
                    data['data'],
                    data['quote'],
                    data['download']
                    ))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error saving data:", e)


for institution, url, result_count, page_count in get_info():
    if page_count <= 120:
        crawl_data(institution, url, result_count, page_count)
    else:
        crawl_data_divided(institution, url, result_count, page_count)