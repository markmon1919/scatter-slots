__author__ = 'MMM'

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path
from datetime import datetime
import sys, time

class Jackpot():

	def __init__(self):
		self.website = 'https://www.helpslot.win/home'
		self.homedir = Path.home()

		if (sys.platform == 'linux'):
			self.exec_path = Path('/usr').joinpath('bin').joinpath('google-chrome')
			self.profile = self.homedir.joinpath('.config').joinpath('google-chrome').joinpath('Default')
		if (sys.platform == 'darwin'):
			self.exec_path = Path('/Applications').joinpath('Applications').joinpath('Google Chrome.app').joinpath('Contents').joinpath('MacOs').joinpath('Google Chrome')
			self.profile = self.homedir.joinpath('Library').joinpath('Application Support').joinpath('Google').joinpath('Chrome').joinpath('Profile 1')
		if (sys.platform == 'windows'):
			self.exec_path = self.homedir.joinpath('AppData').joinpath('Local').joinpath('Google').joinpath('Chrome').joinpath('Application').joinpath('chrome.exe')
			self.profile = self.homedir.joinpath('AppData').joinpath('Local').joinpath('Google').joinpath('Chrome').joinpath('User Data')
		
		options = Options()
		# options.add_argument('--user-data-dir=' + str(self.profile))
		options.add_argument("--no-sandbox")
		options.add_argument("--disable-dev-shm-usage")
		options.add_argument("--headless=new")
		options.add_argument("--disable-popup-blocking")

		if (sys.platform == 'linux' or sys.platform == 'darwin'):
			self.browser = webdriver.Chrome(options = options, service = Service(ChromeDriverManager().install()))
		else:
			self.browser = webdriver.Chrome(options = options, service = Service(executable_path = self.exec_path))
		
		self.now = datetime.now()
		print(self.now)
		self.current_time = self.now.strftime("%H:%M")
		self.start_shift = '14:55' # 2:55 PM
		self.end_shift = '00:00' # 12:00 AM

		self.get_data()

	def get_data(self):

		# target_game = "Fortune Gems 2"
		target_game = "Super Ace"

		try:
		    game_elem = self.browser.find_element(
		        By.XPATH,
		        f"//div[@class='gameName' and normalize-space(text())='{target_game}']"
		    )

		    parent = game_elem.find_element(By.XPATH, "./..")

		    jackpot_span = parent.find_element(By.CLASS_NAME, "jackpotPercentage").find_element(By.TAG_NAME, "span")
		    jackpot_value = jackpot_span.text.strip()

		    # history_percents = self.browser.find_elements(By.CSS_SELECTOR, ".historyDetails.percentage div")
		    # ten_mins = history_percents[0].text
		    # one_hr = history_percents[1].text
		    # three_hrs = history_percents[2].text
		    # six_hrs = history_percents[3].text

		    # print(f"{ target_game }".upper())
		    print(f"Jackpot: {jackpot_value}")
		    # print(f"10 Mins: {ten_mins}")
		    # print(f"1 Hr: {one_hr}")
		    # print(f"3 Hrs: {three_hrs}")
		    # print(f"6 Hrs: {six_hrs}")

		except Exception as e:
			print(f"[Error] Could not extract data for '{target_game}': {e}")


if __name__ == '__main__':
	print('\nJACKPOT')
	print(f'\nCreated by: { __author__ }\n')

	Jackpot()

	print('\n\nDONE...!!!\n')

