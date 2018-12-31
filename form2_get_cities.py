import requests
import json
from pprint import pprint

def get_regions(zipcode, city, county):
    url = 'https://5c71376c-5f5d-40b6-9f7b-75a397d404e0.quotes.iwantinsurance.com/(X(1)S(hjw31k0x4ibehmwa4mt4s0x0))/LocalTerrHelp.asmx/GetRegions'
    knownCategoryValues = f"County,CA,{zipcode}:{county};City,CA,{zipcode}:{city};"
    category = f"Region,CA,{zipcode}"
    data = {"knownCategoryValues":knownCategoryValues,"category":category}
    r = requests.post(url, json=data)
    region = json.loads(r.text)
    return region

def get_counties(zipcode):
    # url = 'https://5c71376c-5f5d-40b6-9f7b-75a397d404e0.quotes.iwantinsurance.com/(X(1)S(hjw31k0x4ibehmwa4mt4s0x0))/LocalTerrHelp.asmx/GetCities'
    url = 'https://5c71376c-5f5d-40b6-9f7b-75a397d404e0.quotes.iwantinsurance.com/(X(1)S(hjw31k0x4ibehmwa4mt4s0x0))/LocalTerrHelp.asmx/GetCounties'
    category = f"County,CA,{zipcode}"
    data = {"knownCategoryValues":"","category":category}
    r = requests.post(url, json=data)
    counties = json.loads(r.text)
    return counties['d']    


if __name__ == "__main__":
    # result = get_regions('90746', 'CARSON', 'LOS ANGELES')
    result = get_counties('90501')
    pprint(result)