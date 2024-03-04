# Import libraries
import re
import time
import requests
from random import uniform
from bs4 import BeautifulSoup
import pandas as pd
from requests.adapters import HTTPAdapter
from fake_useragent import UserAgent

ua = UserAgent()
# Set up a header to get through the web verification
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8,it;q=0.7",
    "User-Agent": str(ua.random)
  }

def get_parent_url(city):
    """
    Get all parent URLs of the specified city.
    :param city: Abbreviation of city name in Pinyin
    :return: All parent urls
    """
    url = f'https://{city}.lianjia.com/zufang'

    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=3))
    s.mount('https://', HTTPAdapter(max_retries=3))
    s.keep_alive = False                                                                          # Close the connection after fulfilling the request.

    html = requests.get(url, headers=headers, timeout=(60, 60))                                   # Get html content
    soup = BeautifulSoup(html.text, 'lxml')                                               # Parse html content
    selector = soup.select('ul[data-target="area"] > li.filter__item--level2')                    # Get content that falls in "area" section
    selector = selector[1:]                                                                       # Skip the first element "不限"-> "All area"
    url_parent_all = []                                                                           # Initiate a parent url list


    # Iterate over the area elements
    for i in selector:
        url_region = 'https://sh.lianjia.com' + i.select('a')[0]['href']                          # Get url of each region
        print(f'url_region: {url_region}')                                                        # e.g. https://sh.lianjia.com/zufang/changning/
        html_region = requests.get(url_region, headers=headers, timeout=(60, 60), verify=False)   # Get html content of the corresponding region
        soup_region = BeautifulSoup(html_region.text, 'lxml')                             # Parse region html content
        num_entries = int(soup_region.select('span.content__title--hl')[0].text)                  # Get the total number of entries in the corresponding region

        if num_entries <= 3000:                                                                   # Set a limit to start web scraping
            print(soup_region.select('div.content__pg'))
            index = soup_region.select('div.content__pg')[0]                                      # Get the page content
            index = str(index)                                                                    # Turn bs4 object into text
            re_pattern = re.compile(r'data-totalpage="(.*?)"')                                    # Compile a regular expression pattern for later use
            index = re.findall(re_pattern, index)[0]                                              # Extract page number
            for j in range(1, int(index)+1):                                                      # Loop through each page
                url_parent = url_region + f'pg{j}'
                url_parent_all.append(url_parent)
                print(url_parent)
            html_region.close()
            t = uniform(1, 2)
            time.sleep(t)                                                                         # Suspend execution for seconds to not get banned

        else:
            print(f'Number of entries: {num_entries}.')
            for i in range (1, 8):                                                                # Iterate further into different rental price range
                url_region_rp = url_region + f'rp{i}/'
                print(url_region_rp)
                html_region_rp = requests.get(url_region_rp, headers=headers, timeout=(60, 60), verify=False)
                soup_region_rp = BeautifulSoup(html_region_rp.text, 'lxml')
                num_entries = int(soup_region_rp.select('span.content__title--hl')[0].text)
                if num_entries > 0:
                    index = soup_region_rp.select('div.content__pg')[0]
                    index = str(index)
                    re_set = re.compile(r'data-totalpage="(.*?)"')
                    index = re.findall(re_set, index)[0]
                    for j in range(1, int(index) + 1):
                        url_parent = url_region + "rp{}/".format(i) + "pg{}".format(j)
                        url_parent_all.append(url_parent)
                        print(url_parent)
                html_region_rp.close()
            t = uniform(1, 2)
            time.sleep(t)
    return url_parent_all


# Get child page of each parent page
def get_detail_url(url_parent_all):
    """
    Iterate over each parent page to get their child pages.
    :param url_parent_all: Extracted parent url list
    :return: child urls of each parent url
    """
    url_detail_all = []

    for url in url_parent_all:
        print(url)
        html = requests.get(url, headers=headers, timeout=(60, 60), verify=False)
        soup = BeautifulSoup(html.text, 'lxml')
        selector = soup.select('div a.content__list--item--aside')
        for i in selector:
            i = i['href']
            i = f'https://{city}.lianjia.com' + i
            url_detail_all.append(i)
            print(i)
        t = uniform(0, 0.01)
        time.sleep(t)
    return url_detail_all


# Get data from extracted child urls
def get_data(url_detail_all):
    """
    Get relevent data from all urls.
    :param url_detail_all: Extracted child urls with details information
    :return: Rental information data of selected categories.
    """
    data = []
    num_error = 0
    for i in url_detail_all:
        try:
            info = {}
            url = i
            print(i)
            html = requests.get(url)
            soup = BeautifulSoup(html.text, 'lxml')
            info['link'] = i
            info['house_code'] = i.split('/')[-1].split('.')[0]                                         # e.g. "/zufang/SH1828411663443820544.html"

            breadcrumb = soup.find('div', class_='bread__nav')
            links = breadcrumb.find_all('a')
            result = [link.text[:-2] for link in links][1:]

            info['district'] = result[0]
            info['subarea'] = result[1]
            info['compound_name'] = result[2]

            info['title'] = soup.select('p.content__title')[0].text.strip()
            info['price'] = soup.select("#aside > div.content__aside--title > span")[0].text

            # aside > div.content__aside--title > span

            Selector1 = soup.find(class_='content__aside__list').find_all('li')
            # lis=Soup.find(class_='content__aside__list').find_all('li')
            # print(lis[0].find(text=True, recursive=False).strip())
            # Selector1 = list(filter(None, Selector1))
            # print(Selector1)

            info['lease_mode'] = Selector1[0].find(text=True, recursive=False).strip()
            info['type_area'] = Selector1[1].find(text=True, recursive=False).strip()
            info['orient_floor'] = Selector1[2].find_all(text=True)[1]

            info['last_maintain_time'] = soup.find(class_='content__subtitle').find(text=True, recursive=False).strip().split('：')[1]


            pattern_geo = r"\{\s*longitude:\s*'(-?\d+(?:\.\d+)?)',\s*latitude:\s*'(-?\d+(?:\.\d+)?)'\s*\}"
            def script_filter(tag):
                return tag.name == 'script' and 'g_conf.coord' in tag.text

            # find the script tag that contains "g_conf.coord"
            script_tag = soup.find(script_filter)

            if script_tag:
                script_text = script_tag.text
                match = re.search(pattern_geo, script_text)
                if match:
                    longitude = match.group(1)
                    lattitude = match.group(2)
                    info["coordinate"] = longitude + ',' + lattitude
            else:
                print("No script tag containing 'g_conf.coord' found.")

            subway_distance_info = soup.find('div', {'id': 'around'}).find_all('ul')[1]
            subway_list = []
            for li in subway_distance_info.find_all("li"):
                spans = li.find_all('span')
                line, name = spans[0].get_text().rsplit('-', 1)
                distance = spans[1].get_text()
                current_str = str([line, name, distance])
                subway_list.append(current_str)

            print(','.join(subway_list))
            info['metro'] = ','.join(subway_list)
            if info['metro'] == '':  # 配套设施为空的情况
                info['metro'] = None

        # 基本信息
            info['area'] = soup.select('li[class^="fl oneline"]')[1].text[3:]
            info['orientation'] = soup.select('li[class^="fl oneline"]')[2].text[3:]
            info['check_in'] = soup.select('li[class^="fl oneline"]')[5].text[3:]
            info['floor'] = soup.select('li[class^="fl oneline"]')[7].text[3:]
            info['has_elevator'] = soup.select('li[class^="fl oneline"]')[8].text[3:]
            info['has_parking'] = soup.select('li[class^="fl oneline"]')[10].text[3:]
            info['water_type'] = soup.select('li[class^="fl oneline"]')[11].text[3:]
            info['electricity_type'] = soup.select('li[class^="fl oneline"]')[13].text[3:]
            info['gas'] = soup.select('li[class^="fl oneline"]')[14].text[3:]
            info['heating'] = soup.select('li[class^="fl oneline"]')[16].text[3:]

            info['lease_period'] = soup.select('li[class^="fl oneline"]')[18].text[3:]
            info['house_visit'] = soup.select('li[class^="fl oneline"]')[21].text[3:]

            # info['house_tags'] = soup.select('p.content__aside--tags')[0].text[1:-1].replace('\n', ', ')
            Selector2 = soup.find('ul', class_='content__article__info2').find_all('li')
            tags = soup.find('p', {'class': 'content__aside--tags'}).find_all(['img', 'i'])
            if not tags:
                info['house_tags'] = None
            else:
                result = [tag.get('alt') or tag.get_text() for tag in tags]
                info['house_tags'] = (',').join(result)

            info['facilities'] = []
            for i in Selector2:
                # print(i['class'])                                                   # 对每一个对象进行处理
                if len(i['class']) == 2 and i.text.strip() != '配套设施':
                    # 仅保留有的配套设施

                    info['facilities'].append(i.text.strip())

            info['facilities'] = ",".join(info['facilities'])  # 列表转换为str
            if info['facilities'] == '':  # 配套设施为空的情况
                info['facilities'] = None

            if not soup.select('.threeline'):  # 房源描述为空的情况
                info['house_desc'] = None
            else:
                info['house_desc'] = soup.select('.threeline')[0].text

            data.append(info)  # 将爬取的信息以字典形式添加到数据列表中
            t = uniform(0, 0.01)
            time.sleep(t)  # 爬一条数据暂停t秒
        except:
            num_error += 1
            print("oops, some errors occured")
        continue
    print("出错数据行数: %d" % (num_error))
    df = pd.DataFrame(data)                                                                                # Convert data into DataFrame format
    return df


# Save the data into 'csv' file
def to_csv(df, table_name):
    """
    Save the scraped data into 'csv' file
    :param df: Converted DataFrame data
    :param table_name: Specified name of the target file
    :return:
    """
    df.to_csv(f'{table_name}', index=False)


city = 'sh'
url_parent_all = get_parent_url(city)
url_detail_all = get_detail_url(url_parent_all)
all_url = pd.DataFrame(url_detail_all, columns=['url'])
to_csv(all_url, '{}_all_url'.format(city))
home_df = get_data(url_detail_all)
to_csv(home_df, '{}_home_data'.format(city))