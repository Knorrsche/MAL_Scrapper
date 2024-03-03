from bs4 import BeautifulSoup
import pandas as pd
import os
import requests
import time
import re
import datetime
import numpy as np


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

        print(f'scraped page {int(i / 50) + 1} from {page_count}')

        if page_count == 1:
            break

        time.sleep(10)

    df = pd.DataFrame(top100_animes, columns=table_header_titles)
    df = clean_data(df)

    csv_path = os.path.dirname(os.path.realpath(__file__))
    df.to_csv(f'{csv_path}/top{page_count * 50}_animes.csv')


def clean_data(df):
    df = date_converter('Date_start', df)
    # TODO: find a suitable way to represent unknown ending dates
    df = date_converter('Date_end', df)
    df = clean_members(df)
    df = clean_score(df)
    return df


def date_formatter(date):
    if date == 'Jan':
        return '01'
    if date == 'Feb':
        return '02'
    if date == 'Mar':
        return '03'
    if date == 'Apr':
        return '04'
    if date == 'May':
        return '05'
    if date == 'Jun':
        return '06'
    if date == 'Jul':
        return '07'
    if date == 'Aug':
        return '08'
    if date == 'Sep':
        return '09'
    if date == 'Oct':
        return '10'
    if date == 'Nov':
        return '11'
    if date == 'Dec':
        return '12'
    raise ValueError('Invalid date format')


def date_converter(column_name, df):

    if not (column_name == 'Date_start' or column_name == 'Date_end'):
        raise ValueError('Invalid column')

    column = df[column_name]
    date_column = column.values
    date_column = [date if date is not np.NaN else '01.01.1970' for date in date_column]
    date_column = [date.strip() if isinstance(date, str) and date.strip() != "" else '01.01.1970' for date in
                   date_column]
    pattern_correct = r'^\d{2}\.\d{2}\.\d{4}$'
    pattern_incorrect = r'^([A-Za-z]{3} )?\d{4}$'
    pattern_correct_end = r'\.\d{4}$'
    invalid_dates = []

    for i in range(len(date_column)):
        if isinstance(date_column[i], str):
            if re.search(pattern_incorrect, date_column[i]):
                splitted_date = date_column[i].split(' ')
                if len(splitted_date) == 1:
                    date_column[i] = f'01.01.{splitted_date[0]}'
                else:
                    date_column[i] = f'01.{date_formatter(splitted_date[0])}.{splitted_date[1]}'
            if not re.search(pattern_correct_end, date_column[i]):
                print(i)
                splitted_date = date_column[i].split('.')
                current_year = datetime.datetime.today().year
                last_year_indexes = str(current_year)[-2:]
                if int(splitted_date[2]) > int(last_year_indexes):
                    date_column[i] = f'{splitted_date[0]}.{splitted_date[1]}.19{splitted_date[2]}'
                else:
                    date_column[i] = f'{splitted_date[0]}.{splitted_date[1]}.20{splitted_date[2]}'

            if not re.search(pattern_correct, date_column[i]):
                invalid_dates.append(date_column[i])
    if invalid_dates:
        raise ValueError(f'Invalid dates found: {invalid_dates}')

    df[column_name] = date_column
    return df


def clean_members(df):
    column = df['Members']
    member_columns = column.values

    df['Members'] = [member.replace(',', '') for member in member_columns]
    return df


def clean_score(df):
    column = df['Score']
    score_columns = column.values

    df['Score'] = [str(score).replace('.', ',') for score in score_columns]
    return df


scrape()
