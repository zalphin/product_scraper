import requests
from bs4 import BeautifulSoup
import csv
import sys
from pprint import pprint
sys.setrecursionlimit(10000)

# Purpose: Generate a CSV with all products on nicedoggies.net
#		   Download appropriate images for the appropriate products

# Create a recursive function to get all URLs with a form
# input: list of URLs to check
# output: List of URLs that are product pages
def find_product_pages(potentialURLs, checkedURLs = []):
	# if potential URLs is empty, return empty array
	if len(potentialURLs) < 1:
		return list()
	# remove the URL to check
	checkURL = potentialURLs.pop()
	print(f'Checking {checkURL}')
	# check if the page has already been looked at
	if checkURL in checkedURLs:
		return find_product_pages(potentialURLs, checkedURLs)
	# Add URL to checked url list
	checkedURLs.append(checkURL)
	
	#Grab the content of the page
	checkPage = BeautifulSoup(requests.get(checkURL).content, 'html.parser')
	contentsTable = checkPage.find_all('table', class_ = 'contentsTable')
	itemContainer = checkPage.find_all('div', class_ = "itemContainer")
	if len(itemContainer) > 0:
		products = find_product_pages(potentialURLs, checkedURLs)
		products.append(checkURL)
		return products
	elif len(contentsTable) > 0:
		aTags = contentsTable[0].find_all('a')
		pageLinks = list(set(map(lambda a: 'https://nicedoggies.net/' + a.attrs["href"], aTags)))
		# pageLinks = pageLinks - potentialURLs - checkedURLs
		pageLinks = [link for link in pageLinks if (link not in potentialURLs) and (link not in checkedURLs)]
		potentialURLs = potentialURLs + pageLinks
		return find_product_pages(potentialURLs, checkedURLs)
	else:
		return find_product_pages(potentialURLs, checkedURLs)

# Start at nicedoggies.net
# get all links in title bar

initialURL = 'https://nicedoggies.net'
initialPage = BeautifulSoup(requests.get(initialURL).content, 'html.parser')
topNav = initialPage.find('div', id = "topNav")
topNavLinks = list(map(lambda link: 'https://nicedoggies.net/' +  link.attrs['href'], topNav.find_all('a')))[:-1]

navPage = topNavLinks
print(f'the lenght of nav links is {len(topNavLinks)}')
listURLs = find_product_pages(navPage)
print(f'{len(listURLs)} product pages found')
with open('pagelinks.txt', 'a') as pageLinks:
	for listURL in listURLs:
		pageLinks.write(listURL)
		pageLinks.write('\n')
sys.exit()

# Open the pagelinks file, remove all duplicates
productPageFile = open('pagelinks.txt', 'r')
productPageList = productPageFile.read().split('\n')
print(len(productPageList))
productPageList = set(filter(None, productPageList))
print(len(productPageList))
productPageFile.close()

with open('product_records.tsv', 'w', newline='') as tsvfile:
	writer = csv.writer(tsvfile, delimiter='\t', lineterminator='\n')
	writer.writerow(["product_name", "product_sku", "product_description", "product_price", "small_image_name", "large_image_name"])
	for productPageURL in productPageList:
		print(f'Extracting data on page: {productPageURL.split("/")[-1]}')
		# Get the page info
		r = requests.get(productPageURL)
		soup = BeautifulSoup(r.content, 'html.parser')
		# Gets all the items on the page (should only be 1)
		itemContainers = soup.find_all('div', class_ = 'itemContainer')
		# Find all the attributes for the item in each item container
		for itemContainer in itemContainers:
			# Product name
			itemName = ''
			itemCode = ''
			itemPrice = 0.00
			itemDescription = ''
			smallImageName = ''
			largeImageName = ''
			
			itemNameContainer = itemContainer.find('div', class_ = 'itemName')
			if not itemNameContainer == None:
				itemName = itemNameContainer.text
			# Item#
			itemCodeContainer = itemContainer.find('div', class_ = 'itemCode')
			if not itemCodeContainer == None:
				itemCode = itemCodeContainer.text[7:]
			# Price
			itemPriceContainer = itemContainer.find('div', class_ = 'itemPrice')
			if not itemPriceContainer == None:
				itemPrice = itemPriceContainer.text
			# Description
			itemDescriptionContainer = soup.find('div', class_ = 'pageText')
			if not itemDescriptionContainer == None:
				itemDescription = itemDescriptionContainer.text
				
			# Image Info
			# Small image
			smallImageContainer = itemContainer.find('img')
			if (not smallImageContainer == None) and ('src' in smallImageContainer.attrs):
				smallImageLink = smallImageContainer.attrs['src']
				smallImageName = smallImageLink.split("/")[-1]
				smallImgData = requests.get(smallImageLink).content
				open(smallImageName, 'wb').write(smallImgData)
				
			largeImageContainer = itemContainer.a
			if (not largeImageContainer == None) and ('href' in largeImageContainer.attrs):
				# Large image
				largeImageLink = itemContainer.a.attrs["href"]
				largeImageName = largeImageLink.split("/")[-1]
				# Download the image
				largeImgData = requests.get(largeImageLink).content
				open(largeImageName, 'wb').write(largeImgData)
			writer.writerow([itemName, itemCode, itemDescription, itemPrice, smallImageName, largeImageName])
		