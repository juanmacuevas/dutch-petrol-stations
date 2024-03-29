import sys
import time	
import csv	
import urllib.parse
import requests
from xml.etree import ElementTree


"""
This script compiles a list of fuel stations with updated prices.
It first loads a csv with a set of squared areas (~60) delimited by NorthWest and SouthEast point coordinates
Then makes two requests to get the fuel station's information in the area (for diesel AND euro95 gasoline)
The data is cleaned and gas stations merged in a list using the 'url' field as key
then saved to a CSV file in the data/ folder

"""


def main():
	times = int(param(1,1)) # default 1 time
	wait_time_minutes = float(param(2,1)) # default 1 minute
	print(60*wait_time_minutes)
	areas_file = 'partitions.csv'
	fetch_and_save_data(areas_file)
	for i in range(times-1):
			print(f'waiting {wait_time_minutes} minutes...')
			time.sleep(60 * wait_time_minutes)
			fetch_and_save_data(areas_file)



current_milli_time = lambda: int(round(time.time() * 1000))

def load_areas_csv(filename):
	with open(filename) as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		line_count = 0
		areas=[]
		for row in csv_reader:
			area = [round(float(x),12) for x in row]
			area = [[area[0],area[1]],[area[2],area[3]]]
			areas.append(area)   
			line_count += 1
		# print(f'partitions.csv has {line_count} areas.')
		return areas

def encode_params(area,type_gas):
	position = {'left':area[0][1],'right':area[1][1],'bottom':area[0][0],'top':area[1][0],'type':type_gas }
	return urllib.parse.urlencode(position)

def list_stations_from_xml(text):
	xml=ElementTree.fromstring(text)
	return [marker.attrib for marker in xml.findall('marker')]

def request_list_stations_in_area(area,type_fuel):
	url = f'https://www.brandstof-zoeker.nl/getxml.fcgi?{encode_params(area,type_fuel)}'
	headers =  {'Connection':'keep-alive','Accept':'application/xml, text/xml, */*; q=0.01','X-Requested-With':'XMLHttpRequest','Sec-Fetch-Mode':'cors','Sec-Fetch-Site':'same-origin', 'Referer':'https://www.brandstof-zoeker.nl/',}
	response = requests.get(url, headers=headers)
	return list_stations_from_xml(response.text)

def request_stations_online(area):
	return request_list_stations_in_area(area,'Euro 95')+request_list_stations_in_area(area,'Diesel')


def formatDate(date):
	months=['januari','februari','maart','april','mei','juni','juli','augustus','september','oktober','november','december']
	day,month,year=date.split()
	day=int(day)
	month = months.index(month)+1
	return f'{year}-{month:02d}-{day:02d}'



def transform_station(s):
	price_key ='price_'+s['type'].replace(" ","").lower()
	updated_key = 'updated_'+s['type'].replace(" ","").lower()
	key = s['url']
	
	return {
	'lat':s['latitude'],
	'lng':s['longitude'],
	'url':key,
	'chain':s['keten'],
	'name':s['naam'],
	'address':s['adres'],
	'postcode':s['pc_cijfer']+s['pc_letter'],
	'place':s['plaats'].lower().capitalize(),
	price_key: s['prijs'],
	updated_key: formatDate(s['datum'])
	}


def load_and_merge_stations(areas):
	stations ={}
	for i,area in enumerate(areas):
		for s in request_stations_online(area):
			if s['priceless']=='1':
				continue
			key = s['url']
			station = stations.get(key,{})
			station.update(transform_station(s))
			stations[key]=station
		# print(f"{i+1}/{len(areas)}")
	stations = [v for k,v in stations.items()]
	return stations


def save_gasolineras_to_csv(gas,output_file):
	with open(output_file, 'w', encoding='utf-8') as output_file:
		keys=['lat','lng','price_diesel','price_euro95','url','name','chain','address','postcode','place','updated_diesel','updated_euro95']
		dict_writer = csv.DictWriter(output_file,fieldnames=keys)
		dict_writer.writeheader()
		dict_writer.writerows(gas)


def param(index,default):
	if len(sys.argv)>index:
		return sys.argv[index]
	else:
		return default


def fetch_and_save_data(areas_file):
	
	print(f'Fetching at {time.strftime("%H:%M:%S")}... ')
	
	start_time=current_milli_time()
	areas = load_areas_csv(areas_file)
	stations = load_and_merge_stations(areas)
	stations = sorted(stations, key=lambda row: (row['lat'],row['lng'],row['url']))

	output_file = f'data/{time.strftime("%Y_%m_%d__%H_%M")}_stations.csv'
	save_gasolineras_to_csv(stations,output_file)

	save_gasolineras_to_csv(stations,'data/stations.csv')
	
	print(f'{(current_milli_time()-start_time)//1000} seconds')


  
if __name__ == "__main__":
	# execute only if run as a script
	main()




   
