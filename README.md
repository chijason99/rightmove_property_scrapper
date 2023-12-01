# rightmove_to_csv

The program is designed to extract property data from [rightmove](https://www.rightmove.co.uk/) via command line with some basic search criteria like location, number of bedrooms and price, as well as retrieving information regarding nearby crimes within a 1-mile radius of each property's location, and save this data to a CSV file.

Currently this only supports finding properties for renting.

# Installation

## Clone the repository

```bash
git clone https://github.com/chijason99/rightmove_to_csv.git

cd rightmove_to_csv
```
## Set up the virtual environment
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install packages.

```bash
# Install virtualenv if not installed
pip install virtualenv

# Create a virtual environment
virtualenv venv

# Activate the virtual environment
# For Windows:
venv\Scripts\activate
# For macOS/Linux:
source venv/bin/activate

```

## Install Dependencies
```bash
pip install -r requirements.txt
```

## Create an account on Geoapify.com

**Disclaimer : I am not sponsored by Geoapify**

Currently, this programme needs to make use of the Geocoding API to get the coordinates of the property, and then use that to search for crimes commited within 1 mile radius of the property.

Creating an account on [Geoapify](https://www.geoapify.com/) is free, and you can enjoy up to 3000 call limits per day, which I believe is more than enough for the usage of this application.

Create a new project on Geoapify after you have created an account, and choose the GeoCoding API, then you will be provided with an API key.

Inside the config.ini file, paste in your API key like this:

```
GEOAPIFY_API_KEY = paste_your_API_key_here
```
And You are good to go!

## Usage
To run the programme, replace the following <variable> with your own search criteria, and then press Enter

```bash
python main.py <location> <radius> <min_bedroom> <max_bedroom> <min_price> <max_price>
```
### Variables Contraint
- location: a string of the place you want to search. Replace the blank space with underscore if any. For example, type in west_brom instead of west brom. You can still type in hyphen if there is any in the name, for example, stratford-upon-avon

- radius: must be a number from this list:[0 , 0.25 , 0.5 , 1 , 3 , 5, 10 , 15 , 20 , 30 , 40], indicating the radius in miles that you want to search for

- min_bedroom: a number between 0 - 10, where 0 represents studio. If you don't want to specify the number of min_bedroom, you can simply use an underscore _

- max_bedroom: a number between 0 - 10, where 0 represents studio. If you don't want to specify the number of max_bedroom, you can simply use an underscore _. Note that the number of max_bedroom must be larger than or equal to the number of min_bedroom if that is specified

- min_price: a number between 100 - 40000, representing the rent per calendar month. If you don't want to specify the number of min_price, you can simply use an underscore _

- max_price: a number between 100 - 40000, representing the rent per calendar month. If you don't want to specify the number of min_price, you can simply use an underscore _. Note that the number of max_price must be larger than or equal to the number of min_price if that is specified

An example: search for properties in London within 1.5 mile radius, from studio to max 1 bedroom, with a maximum price of £1000 pcm

```bash
python main.py london 1.5 0 1 _ 1000
```
After you see the message "saved to csv", you will be able to see the csv file and you can open it with excel to do the comparison you want!

By default, the csv file will be saved next to the main.py file. If you want to change the destination of the csv file, simply go to the config.ini file and paste in your desired download path. **Don't wrap your path with quotation mark, or the file cannot be saved.**

```
download_path = your_own_download_path
```

## Data in the csv file
- address	: the address of the property

- pcm : the rent per month in pound

- type : the type of property. Flat, Semi-Detached, etc

- bedrooms : the number of bedrooms of the property
  
- bathrooms : the number of bathrooms of the property
  
- link : the rightmove link of the property in case you are interested
  
- crime : this is the number of crimes reported within 1 mile radius of the property address. The number is taken using the [data.police.uk](https://data.police.uk/docs/) api


## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.


## Potential Improvements/Future Ideas
1. Currently, the web scrapper can only scrap from the first page of the search, which have around 25 results. This is because selectolax does not support interacting with the page, and the change page function on rightmove does not use a query parameter, which makes it impossible to use selectolax to get the results from other pages. My plan is to change it to Selenium/Playwright/Puppeteer for more functionalities and customisation, but there is not any planned timeline for this yet.

2. There are many other filter on rightmove that you can use, but currently it only supports the variables shown earlier. This is because those are the criteria that I care about the most, and I don't want to make the command too long. Maybe there are some more config I can add to make the search more customizable

3. The map on each rightmove property is lazy loaded, therefore I cannot grab the accurate coordinates using selectolax when scrapping the web. The crime number might be inaccurate as it is using the calculated latitude and longitude from Geoapify to grab the data.
   
4. The crime data in the csv file are all the crimes within 1 mile radius of the property, which makes this data too ambiguious for examining the safety of the area. It would be better and more reasonable to focus on a smaller area around the property. I notice there is a custom area crime api in [data.police.uk](https://data.police.uk/docs/) api, which I might look into and try to get a more relevant crime number
## License

[MIT](https://choosealicense.com/licenses/mit/)

## Legal
From author : [chijason99](https://github.com/chijason99) The use of scrapping technology is not allowed in the [terms and conditions of rightmove](https://www.rightmove.co.uk/this-site/terms-of-use.html). This project is only built for studying and non-commercial purpose.
