# Realtor Estate 0.1
# A web scraper for gathering data relevant to real estate professionals.

# Little note on the imports here... You may need to install tkinter for your OS.
# On Ubuntu you can run apt to install the package python3-tk and you're all set.

# region Imports

import time
import requests
import pytesseract
import pdf2image
import pyap
import webbrowser
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from tkinter import *
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

# region Classes

class HyperlinkManager:

    def __init__(self, text):

        self.text = text

        self.text.tag_config("hyper", foreground="blue", underline=1)

        self.text.tag_bind("hyper", "<Enter>", self._enter)
        self.text.tag_bind("hyper", "<Leave>", self._leave)
        self.text.tag_bind("hyper", "<Button-1>", self._click)

        self.links = {}

    def add(self, action):
        # add an action to the manager.  returns tags to use in
        # associated text widget
        tag = "hyper-%d" % len(self.links)
        self.links[tag] = action
        return "hyper", tag

    def _enter(self, event):
        self.text.config(cursor="hand2")

    def _leave(self, event):
        self.text.config(cursor="")

    def _click(self, event):
        for tag in self.text.tag_names(CURRENT):
            if tag[:6] == "hyper-":
                self.links[tag]()
                return


# endregion Classes

# region Widgets

# Root Tk window
tk_root = Tk()

# Sets the title of the application's window.
tk_root.title("Realtor Estate 0.1")

# Display for script activity
activity_display = Text(tk_root, state=DISABLED)
activity_display.pack(fill=BOTH, expand=YES)
activity_display.insert(END, " ")

hyperlink = HyperlinkManager(activity_display)

# Entry box for commands
command_entry = Entry(tk_root)
command_entry.pack(fill=BOTH)


# endregion Widgets

# region Functions

def update_activity_display(message, display):
    """Adds and updates the message to the supplied display

    :param message: Message to add to activity display
    :param display: The activity display to add text to
    :return: None
    """
    # Display is disabled by default. It must be enabled to add text.
    display.config(state=NORMAL)
    display.insert(END, message + "\n")

    # Scrolls the display to the end, showing the last message.
    display.see(END)

    display.config(state=DISABLED)


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

        update_activity_display("\n\n* Found " + str(len(
            property_addresses)) + " entries for \"" + instrument_type + "\" cases in the Clay"
                                                                         " County database. Compare"
                                                                         " this number to the"
                                                                         " number of populated fields"
                                                                         " for property addresses in"
                                                                         " the generated CSV file to"
                                                                         " reconcile any"
                                                                         " discrepancies that may"
                                                                         " occur in the PDF"
                                                                         " address-parsing process. *\n",
                                activity_display)

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
                update_activity_display(
                    "\nAn invalid address entered into the Clay County GIS address entry field was found.\n"
                    + "It was located in the PDF found here:", activity_display)

                activity_display.config(state=NORMAL)
                activity_display.pack()
                activity_display.insert(INSERT,
                                        "Link to PDF #" + str(
                                            malformed_property_address_counter) + " for Manual Inspection\n",
                                        hyperlink.add(
                                            lambda: webbrowser.open(malformed_property_address_result_page_link)))
                activity_display.config(state=DISABLED)

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


def process_command(command):
    global username
    global password
    global username_requested
    global password_requested
    global date_range_type_requested
    global date_difference
    global start_date_requested
    global start_date
    global end_date_requested
    global end_date
    global credentials_obtained
    global instrument_type_requested
    global instrument_type
    global is_quit

    split_command = command.split()

    if len(split_command) > 0:

        # region Quit Command
        if split_command[0] == "quit":
            is_quit = True
            return "Quitting..."

        # endregion Quit Command

        # region Username Entry
        elif split_command[0] == "login":
            username_requested = True
            return "\n" \
                   "Please enter your username:"

        # endregion Username Command

        # region Help Commands

        elif split_command[0] == "help":
            return "\nAll available commands:" \
                   "\n" \
                   "login: Initializes the user authentication procedure."

        # endregion Help Commands

        # region Password Entry
        elif username_requested:
            username = split_command[0]
            username_requested = False
            password_requested = True
            command_entry.config(show="*")
            return "\nPlease enter your password:"

        # endregion Password Entry

        # region Date Range Type Entry
        elif password_requested:
            password = split_command[0]
            password_requested = False
            command_entry.config(show="")
            date_range_type_requested = True
            return "\nPlease enter a date range. You may choose from any of the following characters:\n" \
                   "(d: A Day Back | w: A Week Back | m: A Month Back\n" \
                   " | h: Half a Year Back | y: A Full Year Back | c: A Custom Date Range)"

        # endregion Date Range Type Entry

        # region Instrument Type Entry
        elif date_range_type_requested:
            date_range_type = split_command[0].strip().lower()
            date_range_type_requested = False

            if date_range_type == 'd':
                date_difference = one_day_back
            elif date_range_type == 'w':
                date_difference = one_week_back
            elif date_range_type == 'm':
                date_difference = one_month_back
            elif date_range_type == 'h':
                date_difference = half_a_year_back
            elif date_range_type == 'y':
                date_difference = one_year_back
            elif date_range_type == 'c':
                start_date_requested = True
                return "\nPlease enter a start date (i.e. 01/01/2019):"
            else:
                return "\nAn invalid date range type was entered. Please restart and try again."

            instrument_type_requested = True
            start_date = date_difference.strftime("%m/%d/%Y")
            end_date = date.today().strftime("%m/%d/%Y")
            return "\nPlease enter an instrument type:"

        # endregion Instrument Type Entry

        # region Start Date Entry
        elif start_date_requested:
            start_date = datetime.strptime(split_command[0].strip(), "%m/%d/%Y").strftime("%m/%d/%Y")
            start_date_requested = False
            end_date_requested = True
            return "\nPlease enter an end date (i.e. 12/31/2019):"

        # endregion Start Date Entry

        # region End Date Entry
        elif end_date_requested:
            end_date = datetime.strptime(split_command[0].strip(), "%m/%d/%Y").strftime("%m/%d/%Y")

            if end_date < start_date:
                return "A start date must be before an end date. Please restart and try again."

            end_date_requested = False
            instrument_type_requested = True
            return "\nPlease enter an instrument type:"

        # endregion End Date Entry

        # region Request Result
        elif instrument_type_requested:
            instrument_type = split_command[0]
            instrument_type_requested = False
            credentials_obtained = True
            command_entry.config(state=DISABLED)
            command_entry.insert(0, "")
            return_pressed_command(activity_display, command_entry)
            command_entry.config(state=NORMAL)
            if authenticated:
                return "\n" \
                       "Data successfully retrieved!"
            else:
                return "\n" \
                       "Data was not successfully retrieved." \
                       " Please try again with a valid instrument and/or login credentials."

            # endregion Request Result

        # region Data Retrieval

        elif credentials_obtained:
            response_status = issue_request()
            if response_status == 200:  # Makes an HTTP post for authentication.
                return "\n" \
                       "\nRequest successfully completed!"
            else:
                return "\n" \
                       "\nRequest was not completed. Please try again with a stable internet connection."

        # endregion Data Retrieval

        # region Command Not Recognized
        else:
            return "\n" \
                   "Command not recognized." \
                   "\n" \
                   "Type \"help\" for list of commands."
        # endregion Command Not Recognized

    # region Username Empty

    elif username_requested:
        return "\n" \
               "Username cannot be empty. Please enter a valid username:"

    # endregion Username Empty

    # region Date Range Entry
    elif password_requested:
        password = ""
        password_requested = False
        command_entry.config(show="")
        date_range_type_requested = True
        return "\nPlease enter a date range. You may choose from any of the following characters:\n" \
               "(d: A Day Back | w: A Week Back | m: A Month Back\n" \
               " | h: Half a Year Back | y: A Full Year Back | c: A Custom Date Range)"

    # endregion Date Range Entry

    # region Data Retrieval

    elif credentials_obtained:
        response_status = issue_request()
        if response_status == 200:  # Makes an HTTP post for authentication.
            return "\n" \
                   "Request successfully completed!"
        else:
            return "\n" \
                   "Request was invalid. Please try again with valid login credentials."

    # endregion Data Retrieval

    # region Command Empty
    else:
        return "Command not specified.\n" \
               "Type \"help\" for list of commands."
    # endregion Command Empty


# region Commands


def return_pressed_command(display, entry):
    global is_quit
    global tk_root

    update_activity_display(process_command(entry.get()), display)

    # Clear the entry after the command has been entered.
    entry.delete(0, END)

    # If we quit, stop the main GUI loop.
    if is_quit:
        tk_root.destroy()


# endregion Commands

# endregion Functions

# region Command Bindings

command_entry.bind("<Return>", lambda event: return_pressed_command(activity_display, command_entry))

# endregion Command Bindings

# region Main Entry Point

if __name__ == "__main__":
    # region Welcome Message

    # Presents the user with a welcome screen after the application has launched.
    update_activity_display("Welcome to Realtor Estate!"
                            "\n"
                            "You can type the command \"login\" below to begin.",
                            activity_display)

    # endregion Welcome Message

    tk_root.mainloop()

# endregion Main Entry Point
