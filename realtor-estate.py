# Little note on the imports here... You may need to install tkinter for your OS.
# On Ubuntu you can run apt to install the package python3-tk and you're all set.

# region Imports


from tkinter import *

# endregion Imports

# region Variables

case_page = "http://recorder.claycogov.com/irecordclient/login.aspx"
username = ""
password = ""
username_requested = False
password_requested = False
credentials_obtained = False
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
    payload = {
        "username": "<USER NAME>",
        "password": "<PASSWORD>",
        "csrfmiddlewaretoken": "<CSRF_TOKEN>"
    }
    return payload


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
            return "\n" \
                   "Data successfully retrieved!"

            # endregion Request Result

        # region Data Retrieval

        elif credentials_obtained:
            if issue_request():  # Makes an HTTP post for authentication.
                return "\n" \
                       "Request finished!"

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
        return "\n" \
               "Password cannot be empty. Please enter a valid password:"

    # endregion Password Empty

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
