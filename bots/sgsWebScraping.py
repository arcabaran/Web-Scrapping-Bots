
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from lxml import etree

import time
import json
import os

from typing import Tuple

from datetime import datetime

class sgsWebScraper:
    """
    Web scrapping app for the website of the sgs
    """
    def __init__(self, key_words: list) -> None:
        self.base_url = 'https://www.sgs.com/en/publications/safeguards?1&page='
        self.key_words = key_words
        
    def extract_and_write(self, driver: webdriver.Chrome) -> None:

        for key_word in self.key_words:
            urls = self.extract_page_urls(driver, key_word)
            urls = self.cheak_scrapped(urls)
            documents, document_table, document_time, document_metadata = self.get_context(driver=driver, urls=urls, key_word=key_word)
            sub_text_dict, sub_json_dict,  sub_pdf_dict, sub_metadata_dict = self.cheak_folders(key_word)
            self.write_data(
                            sub_text_dict=sub_text_dict, 
                            sub_json_dict=sub_json_dict, 
                            sub_metadata_dict = sub_metadata_dict, 
                            doc=documents, 
                            doc_table=document_table, 
                            doc_time=document_time, 
                            metadata_table=document_metadata
                            )
            

    
    def extract_page_urls(self, driver: webdriver.Chrome, key_word: str) -> list:
        """Extracts the urls of the functions that will be scrapped .

        Args:
            driver (webdriver.Chrome): The webdriver that will be connect to the website
            key_word (str): the key words that needs to be searched in the website.

        Returns:
            list: consists of webpages that will be extracted.
        """
        
        searched_key_world = key_word.replace(' ', '%20')
        flag, urls, page_number = True, list(), 1

        while(flag):
            page_url = self.base_url + str(page_number) + '&searchKey=' + searched_key_world
            driver.get(page_url)
            
            while(True):
                try:
                    number = driver.find_element(By.XPATH, '//*[@id="__next"]/main/div[4]/div[1]/div/div[3]').text
                    number = int(number.split(' ')[0])
                    break
                except:
                    time.sleep(3)
            
            if page_number == 1:
                driver.find_element(By.XPATH, '//*[@id="keywordSearch"]').send_keys(Keys.ENTER)
                time.sleep(2)
                number = driver.find_element(By.XPATH, '//*[@id="__next"]/main/div[4]/div[1]/div/div[3]').text
                number = int(number.split(' ')[0])
                
            if number == 0:
                return urls
                    
            for i in range(10):
                try:
                    elem = driver.find_element(By.XPATH, f'//*[@id="__next"]/main/div[4]/div[3]/div/a[{i+1}]').get_attribute('href')
                    urls.append(elem)
                except:
                    return urls

            page_number+=1
        return urls
    

    def cheak_scrapped(self, urls):
        updated_urls = list()
        try:
            f = open(os.path.join(os.path.join(os.path.join('data', 'raw')), 'visited_websites.txt'), "r", encoding="utf-8")
            visited_webpages = f.read().split('\n')
            f.close()
        except:
            visited_webpages = list()
        for url in urls:
            if not url in visited_webpages:
                updated_urls.append(url)    
        
        self.write_to_website_list(urls)
        return updated_urls
    

    def write_to_website_list(self, new_urls: list):
        for url in new_urls:
            try:

                f = open(os.path.join(os.path.join('data', 'raw'), 'visited_websites.txt'), "a", encoding="utf-8")
                f.write(url)
                f.write('\n')
                f.close
            except:
                f = open(os.path.join(os.path.join('data', 'raw'), 'visited_websites.txt'), "w", encoding="utf-8")
                f.write(url)
                f.write('\n')
                f.close
    

    def extract_text(self, driver: webdriver.Chrome) -> str:
        """Extracting page text

        Args:
            driver (webdriver.Chrome): The webdriver that will be connect to the website

        Returns:
            str: The text that is extracted
        """
        text, index = '', 0

        html_content = driver.page_source

        # Parse the HTML content
        tree = etree.HTML(html_content)
        while True:
            index += 1

            # Define the XPath
            xpath = f'//*[@id="__next"]/main/div[{index}]'

            # Extract the content
            content = tree.xpath(xpath)

            # Extract text from the elements
            if content:
                text += content[0].xpath('string()')
            else:
                print("No page content")
                break 
        return text
            
    def extract_number_of_tables(self, driver: webdriver.Chrome) -> int:
        """Calculates number of the tables on the webpage

        Args:
            driver (webdriver.Chrome): The webdriver that will be connect to the website

        Returns:
            int: Number of tables on the website
        """
        number_of_table = 1

        while(True):
            try:
                num = driver.find_element(By.XPATH, f'//*[@id="__next"]/main/div[4]/div[2]/div/div/table[{number_of_table}]/tbody/tr[1]/th[1]').text
                number_of_table += 1
            except:
                number_of_table -= 1
                return number_of_table
        
            
    def extract_tables(self, driver: webdriver.Chrome, document_tables: dict, table_number: int, page_name: str) -> json:
        """Extracts the tables in the webpage

        Args:
            driver (webdriver.Chrome): The webdriver that will be connect to the website
            document_tables (dict): The dict file of the page tables
            table_number (int): number of tables in the website
            page_name (str): The page name of the website

        Returns:
            dict: The dict file of the page tables
        """

        tables = dict()
        for table_id in range(table_number):
            table_dict = dict()
            index = 1
            while(True):
                try:
                    table_column = driver.find_element(By.XPATH, f'//*[@id="__next"]/main/div[4]/div[2]/div/div/table[{table_id+1}]/tbody/tr[1]/th[{index}]'.format(index)).text
                    table_dict[table_column] = list()
                    index += 1
                except:
                    break
            index = 2
            while(True):
                try:
                    for i, column_name in enumerate(table_dict.keys()):
                        i += 1 
                        st = f'//*[@id="__next"]/main/div[4]/div[2]/div/div/table[{table_id+1}]/tbody/tr[{str(index)}]/td[{str(i)}]'
                        row_ = driver.find_element(By.XPATH, st).text
                        if i == 1:
                            for j in range(len(table_dict.keys())): 
                                st = f'//*[@id="__next"]/main/div[4]/div[2]/div/div/table[{table_id+1}]/tbody/tr[{str(index)}]/td[{str(j+1)}]'
                                row_2 = driver.find_element(By.XPATH, st).text
                        table_dict[column_name].append(row_)
                    index += 1
                except:
                    break
            tables['table ' + str(table_id+1)] = table_dict

        
        document_tables[page_name] = json.dumps(tables, indent=4)  

        return document_tables

    def get_context(self, driver: webdriver.Chrome, urls: list, key_word=str) -> Tuple[dict, dict]: 
        """Extracting the urls 

        Args:
            driver (webdriver.Chrome): The webdriver that will be connect to the website
            urls (list): The list that consist of webpages urls that contains the information to scrap

        Returns:
            Tuple[list, list]: The document that consist of the written information on the webpage and the document json that consist of the table of the webpages
        """
        documents = dict()
        document_tables = dict()
        document_time = dict()
        document_metadata = dict()
        for url in urls:
            document_data = dict()

            page_name = url.split('/')[-1]
            driver.get(url)
            print(url)
            text = self.extract_text(driver=driver)
            documents[page_name] = text
            document_time[page_name] = self.get_date(driver, url)
            number_of_table = self.extract_number_of_tables(driver=driver)
            document_tables = self.extract_tables(driver=driver, document_tables=document_tables, table_number=number_of_table, page_name=page_name)


            document_data['name'] = page_name
            document_data['notified_date'] = self.get_date(driver, url)
            document_data['notified_country'] = '-'
            document_data['keyword'] = key_word
            document_data['URL'] = url
            document_metadata[page_name] = document_data


        return documents, document_tables, document_time, document_metadata
    
    def get_date(self, driver, url):
        print('The url: ', url)
        try:
            date_string = driver.find_element(By.XPATH, '//*[@id="__next"]/main/div[3]/div/div[1]/div/span[2]').text
        except:
            try:
                date_string = driver.find_element(By.XPATH, '//*[@id="__next"]/main/div[3]/div/div[1]/div/span').text
            except:
                date_string = 'October 1, 1999'
        # Convert string to datetime object
        date_object = datetime.strptime(date_string, "%B %d, %Y")

        # Format datetime object as YYYY-MM-DD
        formatted_date = date_object.strftime("%Y-%m-%d")

        return formatted_date

    def create_folder(self, folder_name: str) -> None:
        """Creating the folders if the folder is not created yet

        Args:
            folder_name (str): the folder name that will be created
        """
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)   
    
    def cheak_folders(self, key_word: str) -> Tuple[str, str, str]:
        """_summary_

        Args:
            key_word (str): the key word that will be used to name the folder depending on the searched word on the internet

        Returns:
            _type_: the files path that file will be saved
        """
        self.create_folder('data')
        
        raw_dict = os.path.join('data', 'raw')
        self.create_folder(raw_dict)

        name_folder = os.path.join(raw_dict, self.base_url.split('.')[1])
        sub_folder = key_word

        self.create_folder(name_folder)

        sub_dict = os.path.join(name_folder, sub_folder)
        self.create_folder(sub_dict)

        sub_json_dict = os.path.join(sub_dict, 'json')
        self.create_folder(sub_json_dict)

        sub_text_dict = os.path.join(sub_dict, 'text')
        self.create_folder(sub_text_dict)
        
        sub_pdf_dict = os.path.join(sub_dict, 'pdf')
        self.create_folder(sub_pdf_dict)

        sub_metadata_dict = os.path.join(sub_dict, 'metadata')
        self.create_folder(sub_metadata_dict)

        return sub_text_dict, sub_json_dict, sub_pdf_dict, sub_metadata_dict
    

    def write_data(self, sub_text_dict: str, sub_json_dict: str, sub_metadata_dict: str, doc: dict, doc_table: dict, doc_time: dict, metadata_table) -> None:
        """Writing the data into local file path

        Args:
            sub_text_dict (str): The file path that the text file will be saved
            sub_json_dict (str): The file path that the json file will be saved
            doc (dict): the documents that will be saved
            doc_table (dict): the jason that will be saved
        """
        for i, value in doc.items():
            document = value
            file_name = os.path.join(sub_text_dict, doc_time[i] + '-' + i + '.txt')

            with open(file_name, "w", encoding="utf-8") as text_file:
                text_file.write(document)

        for i, value in doc_table.items():
            document = value
            file_name = os.path.join(sub_json_dict, doc_time[i] + '-' + i + '.json')
            
            with open(file_name, 'w') as f:
                json.dump(value, f)
        
        for i, value in metadata_table.items():
            document = value
            file_name = os.path.join(sub_metadata_dict, 'metadata_' + doc_time[i] + '-' + i + '.json')

            with open(file_name, 'w') as f:
                json.dump(value, f)