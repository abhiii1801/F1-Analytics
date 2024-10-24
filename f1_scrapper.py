from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)


def race_results():
    data = {
        'Year': [],
        'Grand Prix': [],
        'Date': [],
        'Winner': [],
        'Car': [],
        'Laps': [],
        'Time': []
    }

    for i in range(1950, 2024):
        print("Year: " + str(i))
        driver.get(f'https://www.formula1.com/en/results/{i}/races')
        try:
            table = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="maincontent"]/div/div[2]/div/div[2]/div[2]/div/div[2]/table/tbody')))
            rows = table.find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, 'td')
                data['Year'].append(i)
                data['Grand Prix'].append(cols[0].get_attribute('textContent').strip())
                data['Date'].append(cols[1].get_attribute('textContent').strip())
                data['Winner'].append(cols[2].get_attribute('textContent').strip())
                data['Car'].append(cols[3].get_attribute('textContent').strip())
                data['Laps'].append(cols[4].get_attribute('textContent').strip())
                data['Time'].append(cols[5].get_attribute('textContent').strip())
            
            print("Data Extracted")
        except:
            print("Error")
    
    return data

def driver_results():
    data = {
        'Year': [],
        'Pos': [],
        'Driver': [],
        'Nationality': [],
        'Car': [],
        'Pts': []
    }

    for i in range(1950, 2024):
        print("Year: " + str(i))
        driver.get(f'https://www.formula1.com/en/results/{i}/drivers')
        try:
            table = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="maincontent"]/div/div[2]/div/div[2]/div[2]/div/div[2]/table/tbody')))
            rows = table.find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, 'td')
                data['Year'].append(i)
                data['Pos'].append(cols[0].get_attribute('textContent').strip())
                data['Driver'].append(cols[1].get_attribute('textContent').strip())
                data['Nationality'].append(cols[2].get_attribute('textContent').strip())
                data['Car'].append(cols[3].get_attribute('textContent').strip())
                data['Pts'].append(cols[4].get_attribute('textContent').strip())
            
            print("Data Extracted")
        except:
            print("Error")
    
    return data



data = race_results()

df = pd.DataFrame(data)
df.to_excel('race.xlsx', index=False, sheet_name='race')
