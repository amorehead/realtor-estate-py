# Little note on the imports here... You may need to install tkinter for your OS.
# On Ubuntu you can run apt to install the package python3-tk and you're all set.

# region Imports


from tkinter import *
import mechanize
import http.cookiejar as cookielib

# endregion Imports

# region Variables

login_url = "http://recorder.claycogov.com/irecordclient/login.aspx"
request_url = "http://recorder.claycogov.com/irecordclient/REALSearchByName.aspx"

username = "GUEST"
password = ""

username_requested = False
password_requested = False
credentials_obtained = False
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
    global authenticated

    # Browser Instantiation
    br = mechanize.Browser()

    # Cookie Jar
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)

    # Browser Options
    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    # The site to which we will navigate while also handling its session.
    br.open("http://recorder.claycogov.com/irecordclient/login.aspx")

    # Selects the first (index zero) form, the login form.
    br.form = list(br.forms())[0]

    # User Credentials
    br.form["USERID"] = username
    br.form["PASSWORD"] = password

    # Login
    br.submit()

    # Proceed to the Search Page
    response = br.open("http://recorder.claycogov.com/irecordclient/REALSearchByName.aspx")
    authenticated = True if "invalid" not in str(response.read()) else False
    if authenticated:
        for form in br.forms():
            update_activity_display('\n' + str(form), activity_display)
    return response


def process_command(command):
    global username
    global password
    global username_requested
    global password_requested
    global credentials_obtained
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

        # region Request Result
        elif password_requested:
            password = split_command[0]
            password_requested = False
            credentials_obtained = True
            command_entry.config(state=DISABLED)
            command_entry.insert(0, "")
            return_pressed_command(activity_display, command_entry)
            if authenticated:
                return "\n" \
                       "Data successfully retrieved!"
            else:
                return "\n" \
                       "Data was not successfully retrieved. Please try again with valid login credentials."

            # endregion Request Result

        # region Data Retrieval

        elif credentials_obtained:
            response = issue_request()
            if response.code == 200:  # Makes an HTTP post for authentication.
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

    # region Password Empty

    elif password_requested:
        password = ""
        password_requested = False
        credentials_obtained = True
        command_entry.config(state=DISABLED)
        command_entry.insert(0, "")
        return_pressed_command(activity_display, command_entry)
        if authenticated:
            return "\n" \
                   "Data successfully retrieved!"
        else:
            return "\n" \
                   "Data was not successfully retrieved. Please try again with valid login credentials."

    # endregion Password Empty

    # region Data Retrieval

    elif credentials_obtained:
        response = issue_request()
        if response.code == 200:  # Makes an HTTP post for authentication.
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
