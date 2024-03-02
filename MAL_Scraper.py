from bs4 import BeautifulSoup
import pandas as pd
import os
import requests
import time

def scrape():
    url = 'https://myanimelist.net/topanime.php'

    try:
        page = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(e)
        return

    soup = BeautifulSoup(page.text, 'html.parser')

    top100 = soup.find('table', class_='top-ranking-table')
    header = top100.find('tr')
    header_titles = header.find_all('td')

    # Header Format:     Rank | Title | Type | Type_count | Date_start | Date_end | Member | Score
    table_header_titles = [title.text for title in header_titles]
    table_header_titles = table_header_titles[0:3]
    table_header_titles.insert(2, "Members")
    table_header_titles.insert(2, "Date_end")
    table_header_titles.insert(2, "Date_start")
    table_header_titles.insert(2, "Type_count")
    table_header_titles.insert(2, "Type")

    print('Insert pagecount to scrape, each page represents 50 entries and the limit is 100:')
    page_count = min(int(input()), 100)

    top100_animes = []
    for i in range(0, page_count * 50, 50):
        url = f'https://myanimelist.net/topanime.php?limit={i}'
        time.sleep(10)
        try:
            page = requests.get(url)
        except requests.exceptions.RequestException as e:
            print(e)
            continue
        soup = BeautifulSoup(page.text, 'html.parser')
        top100 = soup.find('table', class_='top-ranking-table')
        data_set = top100.find_all('tr', class_='ranking-list')
        for data in data_set:
            anime_data_row = [data.find('td', class_='rank ac').get_text().strip()]
            data_title = data.find('td', class_='title al va-t word-break').get_text().strip()

            splitted_data = data_title.split('\n')
            for counter, splitted_data_ in enumerate(splitted_data):
                if counter == 0:
                    anime_data_row.append(splitted_data_.strip())
                elif counter == 1:
                    splitted_type = splitted_data_.split('(')
                    anime_data_row.append(splitted_type[0].strip())
                    anime_data_row.append(splitted_type[1].replace(')', '').replace('eps', '').strip())
                elif counter == 2:
                    splitted_date = splitted_data_.split('-')
                    anime_data_row.append(splitted_date[0].strip())
                    if splitted_date[1] != '':
                        anime_data_row.append(splitted_date[1].strip())
                elif counter == 3:
                    anime_data_row.append(splitted_data_.replace('members', '').strip())
                else:
                    break

            anime_data_row.append(data.find('td', class_='score ac fs14').get_text().strip())
            top100_animes.append(anime_data_row)
        print(f'scraped page {int(i/50) + 1} from {page_count}')

    df = pd.DataFrame(top100_animes, columns=table_header_titles)

    csv_path = os.path.dirname(os.path.realpath(__file__))
    df.to_csv(f'{csv_path}/top{page_count * 50}_animes.csv')

scrape()