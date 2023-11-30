from dataclasses import dataclass, asdict, fields
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
import csv
import sys
import httpx
import asyncio
from selectolax.parser import HTMLParser
import configparser

@dataclass
class Property:
    address:str 
    pcm:int
    type:str | None
    bedrooms:int | None
    bathrooms:int | None
    link:str
    crime: int | None


location_identifier_url = "https://www.rightmove.co.uk/typeAhead/uknostreet/"
rightmove_domain = "https://www.rightmove.co.uk"
headers = {"User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36" }

async def get_location_identifier_from_input(location:str):
    splitted_input = translate_location_to_rightmove_format(location)
    url = location_identifier_url + "".join(splitted_input)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)

            response.raise_for_status()

            json_data = response.json()

            target_location_identifier = json_data["typeAheadLocations"][0]["locationIdentifier"]

            return target_location_identifier
        except httpx.HTTPError as exc:
            print(f"HTTP error occurred: {exc}")

            return None

async def get_crime_data_from_coordinates(latitude:str, longitude:str):
    crime_data_url = f"https://data.police.uk/api/crimes-street/all-crime?lat={latitude}&lng={longitude}"
    
    async with httpx.AsyncClient() as client:
        try:
                response = await client.get(crime_data_url)

                response.raise_for_status()

                json_data = response.json()

                return len(json_data)
        except httpx.HTTPError as exc:
                print(f"HTTP error occurred: {exc}")

                return None

async def get_coordinates_from_address(address:str, api_key:str):
    geoapify_url = f"https://api.geoapify.com/v1/geocode/search?text={address}&apiKey={api_key}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(geoapify_url)

            json_result = response.json()

            coordinates = {"longitude":json_result["features"][0]["properties"]["lon"], "latitude":json_result["features"][0]["properties"]["lat"]}

            return coordinates
        except httpx.HTTPError as exc:
            print(f"HTTP error occurred: {exc}")

            return None
        except Exception:
            print(f"Unexpected error: please check your API key or your credit limit on Geoapify")

def translate_location_to_rightmove_format(location:str) -> str:
    #translate the location from london to LO/ND/ON
    first_six_char = location[0:7].replace("-"," ").replace("_", " ")
    pairs = [first_six_char[i:i+2] for i in range(0, len(first_six_char), 2)]
    translated_string = '/'.join(pairs)
    return translated_string.upper()

def extract_text_from_node(html,selector):
    try:
        return html.css_first(selector).text()
    except AttributeError:
        return None

def parse_html_from_url(url:str):
    response = httpx.get(url, headers = headers)

    html = HTMLParser(response.text)
    
    return html

def get_properties_from_html(html: HTMLParser):
    properties = html.css("div#l-searchResults div.l-searchResult.is-list")

    return properties

def retrieve_property_link(properties: HTMLParser):
    for property in properties:
        yield urljoin(rightmove_domain, property.css_first("a.propertyCard-link").attributes.get("href")) 

async def parse_property_page(html:HTMLParser):
    pcm_text = extract_text_from_node(html, "._1gfnqJ3Vtd1z40MlC0MzXu span")
    extracted_pcm = int(pcm_text.replace("pcm", "").replace("£","").replace(" ", "").replace(",","")) if pcm_text is not None else None

    property = Property(
        address = extract_text_from_node(html, "h1"),
        pcm = extracted_pcm,
        type = get_property_type_for_property(html),
        bedrooms = get_bedroom_count_for_property(html),
        bathrooms = get_bathroom_count_for_property(html),
        link = "",
        crime = "Unknown"
    )

    return asdict(property)

def get_bedroom_count_for_property(html:HTMLParser):
    try:
        bedroom_svg_ele = html.css_first("svg[data-testid=svg-bed]")

        bedroom_text_container = bedroom_svg_ele.parent.parent

        bedroom_text = extract_text_from_node(bedroom_text_container, "dd._1hV1kqpVceE9m-QrX_hWDN  ")

        bedroom_count = int(bedroom_text[1:])

        return bedroom_count
    except Exception:
        return None

def get_bathroom_count_for_property(html:HTMLParser):
    try:
        bathroom_svg_ele = html.css_first("svg[data-testid=svg-bathroom]")

        bathroom_text_container = bathroom_svg_ele.parent.parent

        bathroom_text = extract_text_from_node(bathroom_text_container, "dd._1hV1kqpVceE9m-QrX_hWDN  ")

        bathroom_count = int(bathroom_text[1:])

        return bathroom_count
    except Exception:
        return None

def get_property_type_for_property(html: HTMLParser) :
    try:
        house_svg_ele = html.css_first("svg[data-testid=svg-house]")
        
        property_type_text_container = house_svg_ele.parent.parent

        property_type_text = extract_text_from_node(property_type_text_container, "dd._1hV1kqpVceE9m-QrX_hWDN  ")

        return property_type_text
    except Exception :
        return None

def export_to_csv(location:str,list_of_properties, download_path:str):
    field_name = [field.name for field in fields(Property)]

    with open(f"{download_path if not download_path else ''}{location}_rightmove_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv", "w") as f:
        writer = csv.DictWriter(f, field_name)

        writer.writeheader()
        
        writer.writerows(list_of_properties)

    print("saved to csv")

def is_arg_range_valid(min:int,max:int,arg: int | float):
    if min <= arg <= max:
        return True
    return False

def validate_input(radius:str, min_bedroom:str | None,max_bedroom:str | None,min_price:str | None,max_price:str | None):
    if not is_arg_range_valid(0,40, float(radius)):
        raise ValueError("Error: radius must be between 0 and 40")
    
    if min_bedroom is not None and not is_arg_range_valid(0,10, int(min_bedroom)):
        raise ValueError("Error: min_bedroom must be between 0 and 10 or _ if you dont want to specify")

    if max_bedroom is not None and not is_arg_range_valid(0,10, int(max_bedroom)):
        raise ValueError("Error: max_bedroom must be between 0 and 10 or _ if you dont want to specify")
    
    if(max_bedroom is not None and min_bedroom is not None and int(max_bedroom) < int(min_bedroom)):
        raise ValueError("Error: max_bedroom must be larger than or equal to min_bedroom")

    if min_price is not None and not is_arg_range_valid(100,40000, int(min_price)):
        raise ValueError("Error: min_price must be between 100 and 40000 or _ if you dont want to specify")
    
    if max_price is not None and not is_arg_range_valid(100,40000, int(max_price)):
        raise ValueError("Error: max_price must be between 100 and 40000 or _ if you dont want to specify")
    
    if(min_price is not None and max_price is not None and int(max_price) < int(min_price)):
        raise ValueError("Error: max_price must be larger than or equal to min_price")

async def main():
    if(len(sys.argv) != 7):
        raise ValueError("Please enter correct parameters format: main.py <location> <search_radius> <min_bedroom> <max_bedroom> <min_price> <max_price>")
    
    #load config
    config = configparser.ConfigParser()
    config.read('config.ini')

    GEOAPIFY_API_KEY = config['API']['GEOAPIFY_API_KEY']

    if GEOAPIFY_API_KEY == "":
        raise ValueError("Please add your own geoapify api key in the config.ini file")
    #extracting data from arguments
    location = sys.argv[1]

    radius = sys.argv[2]

    min_bedroom = sys.argv[3] if sys.argv[3] != "_" else None

    max_bedroom = sys.argv[4] if sys.argv[4] != "_" else None

    min_price = sys.argv[5] if sys.argv[5] != "_" else None

    max_price = sys.argv[6] if sys.argv[6] != "_" else None
    
    validate_input(radius, min_bedroom, max_bedroom, min_price, max_price)
    #queries
    radius_query = f"&radius={radius}" if radius != 0 else ""
    
    min_bedroom_query = f"&minBedrooms={min_bedroom}" if min_bedroom is not None else ""
    
    max_bedroom_query = f"&maxBedrooms={max_bedroom}" if max_bedroom is not None else ""

    min_price_query = f"&minPrice={min_price}" if min_price is not None else ""

    max_price_query = f"&maxPrice={max_price}" if max_price is not None else ""

    try:
        location_identifier = await get_location_identifier_from_input(location)
        
        url = f"https://www.rightmove.co.uk/property-to-rent/find.html?searchType=RENT&locationIdentifier={location_identifier}&insId=1{radius_query}{min_price_query}{max_price_query}{min_bedroom_query}{max_bedroom_query}&displayPropertyType=&maxDaysSinceAdded=&sortByPriceDescending=&_includeLetAgreed=on&primaryDisplayPropertyType=&secondaryDisplayPropertyType=&oldDisplayPropertyType=&oldPrimaryDisplayPropertyType=&letType=&letFurnishType=&houseFlatShare="
        
        list_of_properties = []

        html = parse_html_from_url(url)
        properties = get_properties_from_html(html)
        property_urls = retrieve_property_link(properties)
        
        for url in property_urls:
            html = parse_html_from_url(url)
            parsed_property = await parse_property_page(html)
            parsed_property["link"] = url
            
            coordinates_of_property = await get_coordinates_from_address(parsed_property["address"], GEOAPIFY_API_KEY)

            crime_data_near_property = await get_crime_data_from_coordinates(coordinates_of_property["latitude"], coordinates_of_property["longitude"])

            parsed_property["crime"] = crime_data_near_property if crime_data_near_property != 0 else None

            list_of_properties.append(parsed_property)

        download_path = config['PATH']['download_path']
        export_to_csv(location,list_of_properties, download_path)
    except Exception as ex:
        print(f"Unexpected error occurred : {ex}")
        return

if __name__ == "__main__":
    asyncio.run(main())