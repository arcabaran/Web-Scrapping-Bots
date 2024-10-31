import pandas as pd
import time
import os
import json

import io
from PyPDF2 import PdfMerger

from typing import Tuple

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class epingalertWebScraper:
    """_summary_
    """
    def __init__(self, key_words):
        """_summary_

        Args:
            key_words (_type_): _description_
        """
        self.base_url = 'https://www.epingalert.org/en/Search/Index?freeText=' 
        self.key_words = key_words
        
    def extract_and_write(self, driver: webdriver.Chrome) -> None:
        """The main function to extract and write to data locally

        Args:
            driver (webdriver.Chrome): The webdriver that will be connect to the website
        """
        for key_word in self.key_words:
            try:
                self.download_the_file(driver=driver, key_word=key_word)
                df, keys, pdf_list, document_data = self.read_file(key_word=key_word)
                sub_text_dict, sub_json_dict, sub_pdf_dict, sub_metadata_dict = self.cheak_folders(key_word=key_word)

                self.write_data(
                            name_of_the_files=keys, 
                            dataframe=df, 
                            pdf_list=pdf_list,
                            sub_pdf_dict=sub_pdf_dict,
                            sub_text_dict=sub_text_dict, 
                            sub_metadata_dict=sub_metadata_dict,
                            metadata = document_data,
                            name_folder=os.path.join(os.path.join(os.path.join(os. getcwd(), 'data'), 'raw'), self.base_url.split('.')[1])   
                            )

            finally:
                try:
                    os.remove('Notifications.xlsx')
                except:
                    pass
            time.sleep(1)
        
    def download_the_file(self, driver: webdriver.Chrome, key_word: str) -> None:
        """_summary_

        Args:
            driver (webdriver.Chrome): The webdriver that will be connect to the website
            key_word (str): The key word that will be searched on the website
        """
        
        searched_key_world = key_word.replace(' ', '%20')
        page_url = self.base_url + '"' + searched_key_world + '"'
        gotit=driver.get(page_url)
        
        self.wait_to_page_to_load(
            driver=driver,
            xpath='//*[@id="content"]/div/main/div/section/section/div[2]/div/div[2]/div[2]/div[3]/table/tbody/tr[1]/td[2]',
            is_click=False,
            delay=5
        )
        
        gotit = driver.find_element(By.XPATH, '//*[@id="content"]/div/main/div/section/section/div[1]/div[2]/div/button/span')
        gotit.click()  
        
        self.wait_to_page_to_load(
            driver=driver,
            xpath='//*[@id="app"]/div/div[2]/footer/button[2]',
            is_click=True,
            delay=5
        )

    def wait_to_page_to_load(self, driver: webdriver.Chrome, xpath: str, is_click=False, delay: int = 3) -> None:
        """_summary_

        Args:
            driver (webdriver.Chrome): The webdriver that will be connect to the website
            xpath (str): The xpath that will be searched for on the website
            is_click (bool, optional): The bool value to click the alert button on the website. Defaults to False.
            delay (int, optional): The delay that will be wait for website to load. Defaults to 3.
        """
        try:
            myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, xpath)))
            if is_click:
                gotit = driver.find_element(By.XPATH, '//*[@id="app"]/div/div[2]/footer/button[2]')
                gotit.click()     
        except:
            pass
    
    
    def read_file(self, key_word: str) -> Tuple[pd.DataFrame, pd.Series, list]:
        """Reading the excel file and extracting important information to write to txt and the metadata

        Returns:
            Tuple[pd.DataFrame, pd.Series]: The dataframe that hold the inforation to write to txt file and the file names that is combination of the date and title.
        """
        
        df = self.read_excel_file(
            path='Notifications.xlsx',
            delay=3
        )
        
        name_of_the_files = df['Distribution date'].astype(str) + '-' + df['Title']
        df = df[df['Description'].notna()]
        df = df.reset_index(drop=True)
        
        pdf_files_series = df['Notified document'].values
        pdf_files_list = list()

        document_data = dict()
        document_data['name'] = df['Title'].values
        document_data['notified_date'] = df['Distribution date'].astype(str).values
        document_data['notified_country'] = df['Notifying Member'].values
        document_data['URL'] = df['Document symbol'].values
        document_data['keyword'] = list()

        for i in range(len(df)):
            document_data['keyword'].append(key_word)
        
        for i in range(len(pdf_files_series)):
            pdf_files_list.append(str(pdf_files_series[i]).split('\n'))
              
        selected_columns = ['Title', 'Distribution date', 'Final date for comments', 'Notification type','Keywords', 'Description', 'Objectives', 'Notified document']
        for col in selected_columns:
            df[col] = col + ':\n' + df[col].astype(str) + '\n'
            
        df = df[selected_columns]
        df['concatenated'] = df.apply(lambda row: ''.join(map(str, row)), axis=1)

        return df, name_of_the_files, pdf_files_list, document_data
    
    
    def read_excel_file(self, path: str, delay: int = 3) -> pd.DataFrame:
        """Reading the excel file and wait until it reads

        Args:
            path (str): The file path of the excel file
            delay (int, optional): The delay that will be wait for website to load. Defaults to 3.

        Returns:
            pd.DataFrame: The dataframe that holds the information from the website
        """
        while(True):
            temp_path = os.path.split(os.path.dirname(__file__))[0]
            excel_path = os.path.join(os.path.split(temp_path)[0], path)
            try:
                df = pd.read_excel(excel_path)
                return df
            except:
                print('Waiting to load...')
                time.sleep(delay)
    
    def write_data(self, name_of_the_files: pd.Series, dataframe: pd.DataFrame, 
                   pdf_list: list, sub_pdf_dict: str, sub_text_dict: str, sub_metadata_dict: str,name_folder: str, metadata: dict) -> None:
        """Writing the data to the folders and to metadata

        Args:
            name_of_the_files (pd.Series): The file names that will be written in metadata and as the file name
            dataframe (pd.DataFrame): The dataframe that holds the information to be written to the txt files
            sub_text_dict (str): The pathway to the files
            name_folder (str): The main folder name
        """

        for index, row in dataframe.iterrows():
            strings_to_replace = ['/', '\\', ':', '"', '<', '>', '|', '\\n', '\n', '*', '.']

            new_name = self.replace_strings(
                                            name_of_file=name_of_the_files.values[index], 
                                            strings_to_replace=strings_to_replace
                                            )
            
            new_name = new_name[:150]

            name_list = self.read_metadata(name_folder=name_folder)
            self.write_the_data_helper(sub_text_dict=sub_text_dict, 
                                       sub_pdf_dict=sub_pdf_dict, 
                                       sub_metadata_dict=sub_metadata_dict,
                                       new_name=new_name, 
                                       name_list=name_list, 
                                       row=row, 
                                       name_folder=name_folder, 
                                       pdf_list=pdf_list, 
                                       index=index,
                                       metadata=metadata
                                    )
            
    def pdf_merger(self, list_binary_pdf):
        merger = PdfMerger()

        for pdf_bytes in list_binary_pdf:
            pdf_stream = io.BytesIO(pdf_bytes)
            merger.append(pdf_stream)

        merged_pdf_stream = io.BytesIO()
        merger.write(merged_pdf_stream)
    
        return merger
           

    def write_the_data_helper(self, sub_text_dict: str, sub_pdf_dict: str, sub_metadata_dict: str, new_name: str, name_list: list, 
                              row: pd.Series, name_folder: str, pdf_list: list, index: int, metadata: dict):
        """Helper function for the write data function

        Args:
            sub_text_dict (str): The pathway of the files
            new_name (str): The new name of the file
            name_list (list): The filenames on the metadata
            row (pd.Series): The rows on the dataframe to write to txt file one by one
            name_folder (str): the main folder path
        """
        pdfname = os.path.join(sub_pdf_dict, f'{new_name}.pdf')
        if not new_name in name_list:
            if not os.path.exists(pdfname):
                
                list_binary_pdf = list()
                for i in range(len(pdf_list[index])):
                    try:
                    
                        url = pdf_list[index][i]
                        r = requests.get(url, stream=True)
                        if url[-3:] == 'pdf':
                            list_binary_pdf.append(r.content)
                    except:
                        pass

                    
                if list_binary_pdf:
                    try:
                        merger = self.pdf_merger(list_binary_pdf)
                        with open(pdfname, 'wb') as output_file:
                            merger.write(pdfname)
                    except:
                        pass

                filename = os.path.join(sub_text_dict, f'{new_name}.txt')


        filename = os.path.join(sub_metadata_dict, f'metadata_{new_name}.json')     
        if not new_name in name_list:
            if not os.path.exists(filename):
                result_dict = {}
                for key, value in metadata.items():
                    result_dict[key] = value[index]
                print(result_dict)
                with open(filename, 'w') as f:
                    json.dump(result_dict, f)


        filename = os.path.join(sub_text_dict, f'{new_name}.txt')
        if not new_name in name_list:
            if not os.path.exists(filename):
                with open(filename, 'w', encoding="utf-8") as file:
                    file.write(row['concatenated'])

                f = open(os.path.join(name_folder, 'metadata.txt'), "a", encoding="utf-8")
                f.write(new_name)
                f.write('\n')
                f.close

                filename = os.path.join(sub_text_dict, f'{new_name}.txt')

                
            
    def read_metadata(self, name_folder: str) -> list:
        """Reading the meta data

        Args:
            name_folder (str): The main folder name

        Returns:
            list: The name list on the metadata
        """
        try:
            f = open(os.path.join(name_folder, 'metadata.txt'), "r", encoding="utf-8")
            name_list = f.read().split('\n')
            f.close()
        except:
            f = open(os.path.join(name_folder, 'metadata.txt'), "w+", encoding="utf-8")
            f.close()
            name_list = list()
        return name_list

    def replace_strings(self, name_of_file: str, strings_to_replace: list) -> str:
        """The replacing string in the name strings

        Args:
            name_of_file (str): the file name 
            strings_to_replace (list): The strings that is not acceptable for naming 

        Returns:
            str: A new file name
        """
        nan_strings = 1
        for string in strings_to_replace:
            try:
                name_of_file = name_of_file.replace(string, "")
            except:
                name_of_file='01-01-1999 Problemetic Text' + str(nan_strings)
                nan_strings += 1
        return name_of_file

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