# Realtor Estate 1.0
# A web scraper for gathering data relevant to real estate professionals.

# region Imports

import time
import requests
import pytesseract
import pdf2image
import pyap
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import date
from seleniumrequests import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# endregion Imports

# region Variables

login_url = "http://recorder.claycogov.com/irecordclient/login.aspx"
base_search_url = "http://recorder.claycogov.com/irecordclient/"
instrument_type_search_url = "http://recorder.claycogov.com/irecordclient/REALSearchByName.aspx"
gis_url = "https://gisweb.claycountymo.gov/mobile/"

username = "guest"
password = ""

one_day_back = date.today() - relativedelta(days=1)
one_week_back = date.today() - relativedelta(weeks=1)
one_month_back = date.today() - relativedelta(months=1)
half_a_year_back = date.today() - relativedelta(months=6)
one_year_back = date.today() - relativedelta(years=1)

date_difference = one_month_back

start_date = date_difference.strftime("%m/%d/%Y")

end_date = date.today()

instrument_type = "prbt"

username_requested = False
password_requested = False
date_range_type_requested = False
start_date_requested = False
end_date_requested = False
credentials_obtained = False
instrument_type_requested = False
authenticated = False
is_quit = False


# endregion Variables

# region Functions

def issue_request():
    # region Variable Declarations
    global start_date, end_date, \
        instrument_type, property_address, \
        authenticated

    instrument_types = []
    recording_dates = []
    dated_dates = []
    grantors = []
    grantees = []
    result_page_links = []
    property_addresses = []
    property_owner_names = []
    property_owner_addresses = []
    pdf_text = ""
    # endregion Variable Declarations

    # Browser Instantiation
    browser = Chrome(ChromeDriverManager().install())

    # The site to which we will navigate while also handling its session.
    browser.get(login_url)

    # Locates and populates the elements containing the username and password entry fields.
    username_element = browser.find_element_by_id("USERID")
    username_element.send_keys(username)
    password_element = browser.find_element_by_id("PASSWORD")
    password_element.send_keys(password)

    # Login
    password_element.send_keys(Keys.RETURN)
    authenticated = True if "invalid" not in str(browser.page_source) else False

    if authenticated:
        # Navigation to and Selection of Advanced Search
        browser.get(instrument_type_search_url)

        # Ensure Page Elements Have Loaded
        time.sleep(1)

        # Reveal Additional Search Fields
        search_type = browser.find_element_by_id("lbSearchType")
        search_type.click()

        # Ensure Page Elements Have Loaded
        time.sleep(1)

        # Issue an Advanced Search Query
        start_date_field = browser.find_element_by_id("STARTDATE")
        start_date_field.send_keys(start_date)
        end_date_field = browser.find_element_by_id("ENDDATE")
        end_date_field.send_keys(end_date)
        instrument_type_field = browser.find_element_by_id("INSTRUMENT_TYPES")
        instrument_type_field.send_keys(instrument_type)
        search_button = browser.find_element_by_id("SearchButton")
        search_button.click()

        # Harvest the Query
        document_links = set()

        result_page_repeater_ids = set(link.get_attribute("id") for link in browser.find_elements_by_xpath("//a[@href]")
                                       if "PageRepeater" in link.get_attribute("href"))

        for result_page_repeater_id in result_page_repeater_ids:
            result_page_repeater = browser.find_element_by_id(result_page_repeater_id)
            result_page_repeater.click()

            current_page_document_links = set(
                link.get_attribute("href") for link in browser.find_elements_by_xpath("//a[@href]")
                if "PK" in link.get_attribute("href"))

            document_links = document_links | current_page_document_links

        for result_page_link in document_links:
            # Procedurally Extracting Instrument Types, Recording Dates,
            # Dated Dates, Grantors, Grantees, & Property Addresses
            malformed_property_address_counter = 0
            browser.get(result_page_link)
            column_data = browser.find_elements_by_class_name("coldata")

            for column_datum in column_data:
                parsed_datum = column_datum.text.split('\n')
                if malformed_property_address_counter == 0:
                    instrument_types.append(parsed_datum[0])
                elif malformed_property_address_counter == 4:
                    recording_dates.append(parsed_datum[0])
                elif malformed_property_address_counter == 5:
                    dated_dates.append(parsed_datum[0])
                elif malformed_property_address_counter == 9:
                    grantors.append(parsed_datum)
                elif malformed_property_address_counter == 10:
                    grantees.append(parsed_datum)
                malformed_property_address_counter += 1

            view_document_button = browser.find_element_by_id("BTN_VIEW_DOCUMENT")
            on_click = view_document_button.get_attribute("onclick")
            pdf_download_link = base_search_url + str(on_click).split('\'')[1]
            pdf = browser.request("GET", pdf_download_link).content
            pdf_image = pdf2image.convert_from_bytes(pdf)
            for page in pdf_image:
                page_text = pytesseract.image_to_string(page)
                if "Real Estate" in page_text \
                        or "PROPERTY TO BE DISTRIBUTED" in page_text \
                        or "Decedent resided at" in page_text \
                        or "Real Property" in page_text:
                    pdf_text = page_text
                    break

            property_address = pyap.parse(pdf_text, country="US")
            if len(property_address) > 0:
                property_address = str(property_address[0])
            result_page_links.append(result_page_link)
            property_addresses.append(property_address)

        print("\n\n* Found " + str(len(
            property_addresses)) + " entries for \"" + instrument_type + "\" cases in the Clay"
                                                                         " County database. Compare"
                                                                         " this number to the"
                                                                         " number of populated fields"
                                                                         " for property addresses in"
                                                                         " the generated CSV file to"
                                                                         " reconcile any"
                                                                         " discrepancies that may"
                                                                         " occur in the PDF"
                                                                         " address-parsing process. *\n")

        valid_property_address_counter = 0
        malformed_property_address_counter = 1
        for result_page_link, property_address in zip(result_page_links, property_addresses):
            try:
                if len(property_address) == 0:
                    raise NoSuchElementException
                elif len(property_address) > 0:

                    # Navigation to Second Page
                    browser.get(gis_url)

                    # Ensure Page Elements Have Loaded
                    time.sleep(2)

                    # Click Agree
                    agree_field = browser.find_element_by_id("dojox_mobile_Button_0")
                    agree_field.click()

                    # Navigation to Address Search
                    address_search_field = browser.find_element_by_id("searchButton")
                    address_search_field.click()

                    # Ensure Page Elements Have Loaded
                    time.sleep(2)

                    address_search_tab = browser.find_element_by_id("addressTab")
                    address_search_tab.click()

                    # Ensure Page Elements Have Loaded
                    time.sleep(2)

                    search_input_field = browser.find_element_by_id("search_input")

                    # Ensure Page Elements Have Loaded
                    time.sleep(3)

                    # Enter Address
                    search_input_field.send_keys(property_address)

                    # Ensure Page Elements Have Loaded
                    time.sleep(2)

                    # Click Submit
                    search_input_field.send_keys(Keys.RETURN)

                    # Ensure Search Results Have Loaded
                    time.sleep(3)

                    # Harvesting Property Owner Names
                    gis_results_container = browser.find_element_by_id("resultsGeocodeContainer0")
                    for line in gis_results_container.text.split("\n"):
                        if "Current Owner" in line:
                            property_owner_name = line.split(":")[1].strip()
                            property_owner_names.append(property_owner_name)
                            break

                    # Collecting Property Owner Addresses
                    tabs = browser.window_handles

                    for link in gis_results_container.find_elements_by_xpath("//a[@href]"):
                        if "parcelid" in link.get_attribute("href"):
                            link.click()
                            tabs = browser.window_handles
                            browser.switch_to.window(tabs[1])
                            break

                    property_owner_addresses.append(
                        browser.find_element_by_xpath("/html/body/table[2]/tbody/tr[7]/td").text + ', '
                        + browser.find_element_by_xpath("/html/body/table[2]/tbody/tr[9]/td").text)

                    browser.close()
                    browser.switch_to.window(tabs[0])

                    valid_property_address_counter += 1
                else:
                    property_owner_names.append([])
                    property_owner_addresses.append([])

            except NoSuchElementException:
                malformed_property_address_result_page_link = result_page_link
                print(
                    "\nAn invalid address entered into the Clay County GIS address entry field was found.\n"
                    + "It was located in the PDF found here:")

                print("Link to PDF #" + str(
                    malformed_property_address_counter) + " for Manual Inspection:\n" +
                      malformed_property_address_result_page_link)

                property_owner_names.append([])
                property_owner_addresses.append([])

                malformed_property_address_counter += 1
                pass

    # Exporting Scraped Data to CSV File
    df_data = [instrument_types, recording_dates, dated_dates, grantors, grantees,
               result_page_links, property_addresses, property_owner_names, property_owner_addresses]

    df = pd.DataFrame(data=df_data).T

    df.columns = ["Instrument Type", "Recording Date", "Dated Date",
                  "Grantor(s)", "Grantee(s)", "Result Page Link",
                  "Property Address", "Current Property Owner Name", "Owner Mailing Address"]

    df.to_csv("Realtor Estate Data Export (" + str(date.today()) + ").csv")

    # Cleaning Up the Browser Instance
    browser.close()

    return requests.get(instrument_type_search_url).status_code


# endregion Commands

# endregion Functions

# region Main Entry Point

if __name__ == "__main__":
    # region Welcome Message

    # Presents the user with a welcome screen after the application has launched.
    print("Welcome to Realtor Estate!"
          "\n"
          "You can type the command \"login\" below to begin.")

    # endregion Welcome Message

# endregion Main Entry Point
