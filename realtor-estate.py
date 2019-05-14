# Little note on the imports here... You may need to install tkinter for your OS.
# On Ubuntu you can run apt to install the package python3-tk and you're all set.

# region Imports

import time
import requests
from datetime import date, timedelta
from tkinter import *
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# endregion Imports

# region Variables

login_url = "http://recorder.claycogov.com/irecordclient/login.aspx"
instrument_type_search_url = "http://recorder.claycogov.com/irecordclient/REALSearchByName.aspx"
address_search_url = "https://gisweb.claycountymo.gov/mobile/"

username = "guest"
password = ""
first_day_of_previous_month = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
start_date = first_day_of_previous_month.strftime("%m/%d/%Y")
last_day_of_previous_month = date.today().replace(day=1) - timedelta(days=1)
end_date = last_day_of_previous_month.strftime("%m/%d/%Y")
instrument_type = "prbt"

username_requested = False
password_requested = False
credentials_obtained = False
instrument_type_requested = False
authenticated = False
is_quit = False

# endregion Variables

# region Widgets

# Root Tk window
tk_root = Tk()

# Sets the title of the application's window.
tk_root.title("Realtor Estate 0.1")

# Display for script activity
activity_display = Text(tk_root, state=DISABLED)
activity_display.pack(fill=BOTH, expand=YES)
activity_display.insert(END, " ")

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
    global start_date
    global end_date
    global instrument_type
    global authenticated

    # Browser Instantiation
    options = Options()
    options.headless = False
    browser = webdriver.Chrome(options=options)

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
        update_activity_display('\n' + str(browser.page_source), activity_display)

        # Navigation to Second Page
        browser.get(address_search_url)

        # Ensure Page Elements Have Loaded
        time.sleep(3)

        # Click Agree
        agree_field = browser.find_element_by_id("dojox_mobile_Button_0")
        agree_field.click()

        # Search by Address
        address_search_field = browser.find_element_by_id("searchButton")
        address_search_field.click()
        address_search_tab = browser.find_element_by_id("addressTab")
        address_search_tab.click()

        # Ensure Page Elements Have Loaded
        time.sleep(1)

    return requests.get(instrument_type_search_url).status_code


def process_command(command):
    global username
    global password
    global username_requested
    global password_requested
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
            return "Please enter your password:"

        # endregion Password Entry

        # region Instrument Type Entry
        elif password_requested:
            password = split_command[0]
            password_requested = False
            instrument_type_requested = True
            return "Please enter an instrument type:"

        # endregion Instrument Type Entry

        # region Request Result
        elif instrument_type_requested:
            instrument_type = split_command[0]
            instrument_type_requested = False
            credentials_obtained = True
            command_entry.config(state=DISABLED)
            command_entry.insert(0, "")
            return_pressed_command(activity_display, command_entry)
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
                       "Request successfully completed!"
            else:
                return "\n" \
                       "Request was not completed. Please try again with a stable internet connection."

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

    # region Instrument Type Entry
    elif password_requested:
        password = ""
        password_requested = False
        instrument_type_requested = True
        return "Please enter an instrument type:"

    # endregion Instrument Type Entry

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
