import pandas as pd
import time
import os
import json
import re 
from datetime import datetime  
  
import io
from PyPDF2 import PdfMerger

from typing import Tuple, List

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ulWebScrapping():
    def __init__(self,key_words):
        self.base_url = "https://www.ul.com/news/regulatory-updates?title={}&page={}"
        self.key_words = key_words

    def extract_and_write(self,driver):
        #Main caller function for scraping
        for word in self.key_words:
            time.sleep(5)
            links=self.get_all_links(driver,word)
            if len(links)<1:
                print("Bu kelime bulunamadı {}".format(word))
                continue
            print("extract girdi {}".format(word))
            self.extract_page(links,driver,word)

    def get_all_links(self,driver,word)->List:
        #Getting all the related links with given keyword.
        driver.get(self.base_url.format(word,0))
        try:
            page_num=driver.find_element(By.XPATH,'//*[@id="main-content"]/section/div[2]/div/div/div/div[2]/section[2]/div/nav/div/span/span[2]')
            page_num=int(page_num.text[-1])
        except:
            page_num=1
        links=[]
        for i in range(page_num):
            try:
                driver.get(self.base_url.format(word,i))

                element_amount_in_page=len(driver.find_elements(By.XPATH,'//*[@id="main-content"]/section/div[2]/div/div/div/div[2]/section[1]/div/div/div'))

                for element in range(element_amount_in_page):
                    elem = driver.find_element(By.XPATH, f'/html/body/div[1]/div[3]/div[2]/div/main/section/div[2]/div/div/div/div[2]/section[1]/div/div/div[{element+1}]/div/a').get_attribute('href')
                    links.append(elem)
            except:
                pass
        return links

    def extract_page(self,url_list,driver,keyword):
        #Extracting the page content as well as calling table parser with using given link list.
        text=""
        for url in url_list:
            driver.get(url)

            date= driver.find_element(By.XPATH, '/html/body/div[1]/div[3]/div[2]/div/main/section[1]/p').text
            date=datetime.strptime(date, "%B %d, %Y")
            date=date.strftime("%Y-%m-%d")
            title=str(date)+str(driver.find_element(By.XPATH, '/html/body/div[1]/div[3]/div[2]/div/section/div/div/div[1]/div/h1').text) 
            
            all_paragraphs=driver.find_element(By.XPATH,f'//*[@id="main-content"]/section[2]/div[2]/div')

            child_nodes = all_paragraphs.find_elements(By.XPATH, './*')  
            
            text_list = []  
            
            for node in child_nodes:  
                if node.tag_name == 'p' or node.tag_name == 'ul':  
                    text_list.append(node.text)  
            
            text = '\n'.join(text_list)  
            json_data = self.table_parser(driver)

            self.write(keyword=keyword,text_data=str(text),title=title,json_data=json_data)


    
    def table_parser(self,driver):
        #Parsing table as a json. 
        rows = []  
        tables=[]
        
        for i in range(10):#farazi
            try:
                table=driver.find_element(By.XPATH,'//*[@id="DataTables_Table_{}"]'.format(i))
                for row_element in table.find_elements(By.XPATH,'.//tr'):  
                    row = [data.text for data in row_element.find_elements(By.XPATH,'.//td')]  
                    rows.append(row)  
                
                headers = rows[0]  
                rows = rows[1:]  
                
                table_data = []  
                for row in rows:  
                    table_data.append(dict(zip(headers, row)))  
                
                json_data = json.dumps(table_data, indent=4)  
                tables.append(json_data)
            except:
                pass
                
        return tables
        

    def write(self,text_data,title,keyword,json_data):
        #Write function for both json and txt files
        title=self.clean_folder_name(title)
        file_path = 'data/raw/ul/{}'.format(keyword)
        if not os.path.exists(file_path):  
            os.makedirs(file_path)  
        

        subdirectories = ['json', 'text', 'pdf']  
        for subdir in subdirectories:  
            subdir_path = os.path.join(file_path, subdir)  
            if not os.path.exists(subdir_path):  
                os.makedirs(subdir_path)  


        with open(file_path+"/text/{}.txt".format(title), 'w', encoding="utf-8") as file:  
            file.write(text_data)  
        count=1
        time.sleep(5)
        for table in json_data:
            with open(file_path+"/json/{}-table{}.json".format(title,count), 'w', encoding="utf-8") as json_file:  
                json_file.write(table)
        file.close()
        try:json_file.close()
        except:pass

    def clean_folder_name(self,folder_name):  
        #Clean the folder name for possible issues
        pattern = '[\\\\/:*?"<>|]'  
        cleaned_folder_name = re.sub(pattern, '_', folder_name)  

        max_filename_length = 244  
        if len(cleaned_folder_name) > max_filename_length:  
            cleaned_folder_name = cleaned_folder_name[:max_filename_length]  
        return cleaned_folder_name  