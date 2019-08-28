import yaml
import sys
from bs4 import BeautifulSoup

from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from datetime import datetime
from emails import send_email

def _scrape_seat_sale_prices_into_list(page_to_be_scraped):

    soup = BeautifulSoup(page_to_be_scraped, 'lxml')
    prices = []

    for a_tag in soup.find_all('a'):

        values = {}
        for p_tag in a_tag.find_all('p'):

            name = '-'.join(p_tag['class'])
            values[name] = p_tag.string

        if values:
            prices.append(values)

    return prices
    

def get_flight_details(driver, number_of_weeks):

    list_of_prices = []

    for x in range(number_of_weeks):

        list_of_prices += _scrape_seat_sale_prices_into_list(driver.page_source)
        nextScheduleButton = driver.find_element_by_xpath("//div[@class='next-schedule']//a[@aria-label='Next Week']")
        nextScheduleButton.click()

    list_of_prices += _scrape_seat_sale_prices_into_list(driver.page_source)

    return list_of_prices


def find_month_location(driver, month):

    leftMonth = driver.find_element_by_xpath("//table[@class='month1']//thead//tr[@class='caption']//td[@class='month-name']")
    rightMonth = driver.find_element_by_xpath("//table[@class='month2']//thead//tr[@class='caption']//td[@class='month-name']")

    nextMonthButton = driver.find_element_by_xpath("//div[@class='next-month']//a[@class='next']")

    while(month != leftMonth.text and month != rightMonth.text):
        sleep(2)
        nextMonthButton.click()

    if leftMonth.text == month:
        return 'month1'
    else:
        return 'month2'


def select_start_day(driver, month, start_day):

    day_in_menu = driver.find_element_by_xpath("//table[@class='{0}']//tbody//tr//td//div[text()='{1}']".format(month, start_day))
    
    if day_in_menu.get_attribute('class') == 'day toMonth  invalid':
        sys.exit("Invalid start date. Please try again")

    sleep(2)
    day_in_menu.click()
    return

def get_datetime_object(date_string):

    date_object = datetime.strptime(date_string, '%m-%d-%y')
    
    if date_object < datetime.now():
        sys.exit("Invalid start date. Please try again")

    return date_object

def process_flights(flights, origin, destination):

    processedFlights = {'origin' : origin, 'destination' : destination, 'flights' : {}}

    for flight in flights:
        month = (flight['month'])[-3:]
        day = flight['day']
        price = flight['price-lowFareAmt']
    
        processedFlights['flights'].setdefault(month, []).append("{0} {1}: {2}\n".format(month, day, price))

    return processedFlights


def main():

    config = yaml.safe_load(open('config.yaml'))

    date_object = get_datetime_object(config['flight']['start_date'])
    start_month = date_object.strftime('%B %Y')
    start_day = date_object.strftime('%#d')

    chromedriver_path = config['selenium']['chromedriver_path']
    driver = webdriver.Chrome(executable_path=chromedriver_path)
    driver.get(config['selenium']['website_home'])

    one_way_trip_button = driver.find_element_by_xpath("//input[@id='oneWayTrip']/following-sibling::ins[@class='iCheck-helper']")
    one_way_trip_button.click()

    flying_from = driver.find_element_by_id('fromInput')
    flying_from.send_keys(config['flight']['origin'], Keys.ENTER)
    flying_to = driver.find_element_by_id('toInput')
    flying_to.send_keys(config['flight']['destination'], Keys.ENTER)

    start_date_menu = driver.find_element_by_id('startDateNew')
    start_date_menu.click()

    month = find_month_location(driver, start_month)
    select_start_day(driver, month, start_day)

    search_flights_button = driver.find_element_by_id('searchButton')
    sleep(2)
    search_flights_button.click()

    sleep(2)
    flights = get_flight_details(driver, config['flight']['number_of_weeks'])

    flight_details = process_flights(flights, config['flight']['origin'], config['flight']['destination'])
    send_email(config['email'], flight_details)

main()