#!/usr/bin/env python2.7

# Author: m8r0wn
# Description: Python script to interact with Pastebin API

import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error


class paste_it():
	#Class Variables

	#Pastebin API Key
	api_dev_key = ''
	#Pastebin Username
	username = ''
	#Pastebin Password
	password = ''
	#Max results
	api_results_limit = 25  # default=50, min=1, max=1000

	def user_key(self):
		#create user key
		user_key_data = {'api_dev_key': self.api_dev_key,
						 'api_user_name': self.username,
						 'api_user_password': self.password}
		req = urllib.request.urlopen('https://pastebin.com/api/api_login.php',
							  urllib.parse.urlencode(user_key_data).encode('utf-8'), timeout=7)
		return req.read().decode()

	def list_trending(self):
		#list Trending Pastes, max of 18 results allowed:
		api_option = 'trends'
		data = {'api_dev_key': self.api_dev_key,
				'api_option': api_option}
		req = urllib.request.urlopen('https://pastebin.com/api/api_post.php',
							  urllib.parse.urlencode(data).encode('utf-8'), timeout=7)
		return req.read()

	def apiuser_pastes(self):
		#list API user's Pastes:
		api_option = 'list'
		data = data = {'api_dev_key': self.api_dev_key,
					   'api_user_key': self.user_key(),
					   'api_option': api_option,
					   'api_results_limit': self.api_results_limit}
		req = urllib.request.urlopen('https://pastebin.com/api/api_post.php',
							  urllib.parse.urlencode(data).encode('utf-8'), timeout=7)
		return req.read().decode()

	def apiuser_details(self):
		#list API user's details:
		api_option = 'userdetails'
		data = {'api_dev_key': self.api_dev_key,
				'api_user_key': self.user_key(),
				'api_option': api_option,
				'api_results_limit': self.api_results_limit}
		req = urllib.request.urlopen('https://pastebin.com/api/api_post.php',
							  urllib.parse.urlencode(data).encode('utf-8'), timeout=7)
		return req.read().decode()

	def show_apiuser_paste(self, paste_key):
		#Print Raw paste created by api_user
		api_option = 'show_paste'
		api_paste_key = paste_key
		data = {'api_dev_key': self.api_dev_key,
				'api_user_key': self.user_key(),
				'api_option': api_option,
				'api_paste_key': api_paste_key}
		req = urllib.request.urlopen('https://pastebin.com/api/api_raw.php',
							  urllib.parse.urlencode(data).encode('utf-8'), timeout=7)
		return req.read().decode()

	def show_paste(self, paste_key):
		#Print Raw paste
		req = urllib.request.urlopen('https://pastebin.com/raw/'+paste_key, timeout=7)
		return req.read()

	def delete_paste(self, paste_key):
		#Delete one of API user's pastes
		api_option = 'delete'
		api_paste_key = paste_key
		data = {'api_dev_key': self.api_dev_key,
				'api_user_key': self.user_key(),
				'api_option': api_option,
				'api_paste_key': api_paste_key}
		req = urllib.request.urlopen('https://pastebin.com/api/api_post.php',
							  urllib.parse.urlencode(data).encode('utf-8'), timeout=7)
		return req.read().decode()

	def create_paste(self, data, name='title'):
		#Create paste on api user's account
		api_option = 'paste'
		api_paste_code = data  # paste text body
		api_paste_private = 1  # 0=public, 1=unlisted, 2=private
		api_paste_name = name  # title of paste
		# available: N=never, 10M=10min, 1H=1hour, 1D=1Day, 1W=1week, 2W=2weeks, 1M=1Month, 6M=6months, 1Y=1year
		api_paste_expire_date = '1D'
		# text=None, mysql-MYSQL, perl=Perl, python=Python, sql=SQL, vbscript=VBscript, xml=XML, html4strict=HTML, html5=HTML5,
		api_paste_format = 'text'
		data = {'api_dev_key': self.api_dev_key,
				'api_user_key': self.user_key(),
				'api_option': api_option,
				'api_paste_code': api_paste_code,
				'api_paste_private': api_paste_private,
				'api_paste_name': api_paste_name,
				'api_paste_expire_date': api_paste_expire_date,
				'api_paste_format': api_paste_format}
		req = urllib.request.urlopen('https://pastebin.com/api/api_post.php',
							  urllib.parse.urlencode(data).encode('utf-8'), timeout=7)
		return req.read().decode()

	#The following requires your source IP address to be white-listed
	def scraper(self):
		#Fetch most recent pastes
		#Add ?limit=# to limit responses, max=250, default=50
		req = urllib.request.urlopen(
			'https://pastebin.com/api_scraping.php', timeout=7)
		return req.read()

	def scraper_paste(self, paste_key):
		req = urllib.request.urlopen(
			'https://pastebin.com/api_scrape_item.php?i=' + paste_key, timeout=7)
		return req.read()

	def scraper_paste_metadata(self, paste_key):
		req = urllib.request.urlopen(
			'https://pastebin.com/api_scrape_item_meta.php?i=' + paste_key, timeout=7)
		return req.read()


#Example Usage:
    #List trending pastes
# try:
#     paste = paste_it()
#     print paste.list_trending()
# except Exception as e:
#     print "[!] API Error:", e
