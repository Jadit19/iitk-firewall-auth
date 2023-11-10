# Imports required
import argparse
import getpass
import logging
import re
import requests
import signal
import time
from typing import Tuple, Union

# URL constants
ONE_ONE_ONE_ONE = "http://1.1.1.1/"
ONE_ONE_ONE_ONE_HTTPS = "https://1.1.1.1/"


class Parser:
    """Argument parser for firewall.py

    Attributes
    ----------
    >>> username  : str  # IITK CC Username
    >>> password  : str  # IITK CC Password
    >>> verbose   : bool # Logging to console, defaults to True
    >>> retry     : int  # Seconds to wait before retrying, defaults to 60
    >>> keepalive : int  # Seconds to wait between keepalives, defaults to 2200

    Methods
    -------
    >>> __init__()        # Initialize the parser
    >>> __add_args()      # Add arguments to the parser
    >>> __parse_args()    # Parse the arguments
    >>> __validate_args() # Validate the arguments
    """

    def __init__(self) -> None:
        """Constructor for Parser

        Parameters
        ----------
        >>> None

        Returns
        -------
        >>> None
        """
        self.__parser = argparse.ArgumentParser(description="Login to IITK network")
        self.__add_args()
        self.__parse_args()
        self.__validate_args()

    def __add_args(self) -> None:
        """Add arguments to the parser

        Parameters
        ----------
        >>> None

        Returns
        -------
        >>> None
        """
        self.__parser.add_argument("-u", "--username", help="Username", type=str)
        self.__parser.add_argument("-p", "--password", help="Password", type=str)
        self.__parser.add_argument(
            "-v", "--verbose", help="Verbose", type=bool, default=True
        )
        self.__parser.add_argument(
            "-r",
            "--retry",
            help="Seconds to wait before retrying",
            type=int,
            default=60,
        )
        self.__parser.add_argument(
            "-k",
            "--keepalive",
            help="Seconds to wait between keepalives",
            type=int,
            default=2200,
        )

    def __parse_args(self) -> None:
        """Parse the arguments

        Parameters
        ----------
        >>> None

        Returns
        -------
        >>> None
        """
        args = self.__parser.parse_args()
        self.username: str = args.username
        self.password: str = args.password
        self.verbose: bool = args.verbose
        self.retry: int = args.retry
        self.keepalive: int = args.keepalive

    def __validate_args(self) -> None:
        """Validate the arguments

        1. Apart from the username and password, all other arguments are optional.
        2. If not provided, they are set to their default values.
        3. Username and password are prompted for if not provided.

        Parameters
        ----------
        >>> None

        Returns
        -------
        >>> None
        """
        if self.username is None:
            self.username = input("Username: ")
        if self.password is None:
            self.password = getpass.getpass("Password: ")
        if self.retry < 0:
            self.retry = 60
        if self.keepalive < 0:
            self.keepalive = 2200


class Console:
    """Logging to console.

    Attributes
    ----------
    >>> __verbose : bool # Logging to console, defaults to False

    Methods
    -------
    >>> __init__()             # Initialize the logger
    >>> log(message: str)      # Log message to console
    >>> error(message: str)    # Log error message to console
    >>> warn(message: str)     # Log warning message to console
    """

    def __init__(self, verbose: bool = True) -> None:
        """Constructor for Console

        Parameters
        ----------
        >>> verbose : bool # Logging to console, defaults to False

        Returns
        -------
        >>> None
        """
        self.__verbose = verbose
        logging.basicConfig(
            format="\033[92m[%(levelname)s]\033[0m  : %(message)s",
            level=logging.INFO,
        )
        logging.basicConfig(
            format="\033[91m[%(levelname)s]\033[0m : %(message)s",
            level=logging.ERROR,
        )
        logging.basicConfig(
            format="\033[96m[%(levelname)s]\033[0m: %(message)s",
            level=logging.WARNING,
        )

    def log(self, message: str) -> None:
        """Log message to console

        Parameters
        ----------
        >>> message : str

        Returns
        -------
        >>> None
        """
        if self.__verbose:
            logging.info(message)

    def error(self, message: str) -> None:
        """Error message to console

        Parameters
        ----------
        >>> message : str

        Returns
        -------
        >>> None
        """
        if self.__verbose:
            logging.error(message)

    def warn(self, message: str) -> None:
        """Warning message to console

        Parameters
        ----------
        >>> message : str

        Returns
        -------
        >>> None
        """
        if self.__verbose:
            logging.warning(message)


class Authenticator:
    """Authenticator for IITK network

    Attributes
    ----------
    >>> __parser     : Parser   # Argument parser
    >>> __console    : Console  # Console logger
    >>> __logged_in  : bool     # Logged in status
    >>> __logout_url : str      # URL to logout

    Methods
    -------
    >>> __init__()           # Initialize the authenticator
    >>> __interupt_handler() # Handle SIGINT
    >>> __state_check()      # Check if logged in
    >>> __login()            # Login to the network
    >>> __keepalive()        # Send keepalive requests
    >>> run()                # Run the authenticator
    """

    def __init__(self) -> None:
        """Constructor for Authenticator

        Parameters
        ----------
        >>> None

        Returns
        -------
        >>> None
        """
        self.__parser = Parser()
        self.__console = Console(verbose=self.__parser.verbose)
        self.__logged_in: bool = False
        self.__logout_url = ""
        signal.signal(signalnum=signal.SIGINT, handler=self.__interupt_handler)

    def __interupt_handler(self, sig, frame) -> None:
        """Interrupt handler for SIGINT

        Parameters
        ----------
        >>> sig   : int       # Signal number
        >>> frame : FrameType # Frame

        Returns
        -------
        >>> None
        """
        if self.__logged_in:
            try:
                response = requests.get(
                    self.__logout_url, headers={"User-Agent": "Mozilla/5.0"}
                )
            except:
                self.__console.error(f"Cannot open URL: {self.__logout_url}")
            if response.status_code == 200:
                self.__console.log("Successfully logged out")
        else:
            self.__console.log("Exiting")
        exit(code=0)

    def __state_check(self) -> Tuple[bool, requests.Response]:
        """Check if logged in

        Parameters
        ----------
        None

        Returns
        -------
        >>> status   : bool              # Logged in status
        >>> response : requests.Response # Response from the server
        """
        self.__console.log("Checking state")
        while True:
            try:
                response = requests.get(
                    ONE_ONE_ONE_ONE, headers={"User-Agent": "Mozilla/5.0"}
                )
            except requests.exceptions.RequestException:
                self.__console.error(f"Cannot open URL: {ONE_ONE_ONE_ONE}.  Retrying")
                continue
            if response.status_code == 200:
                break
        if response.url == ONE_ONE_ONE_ONE_HTTPS:
            return True, response
        else:
            return False, response

    def __login(
        self, response: requests.Response
    ) -> Tuple[bool, Union[requests.Response, None]]:
        """Login to the network

        Parameters
        ----------
        >>> response : requests.Response

        Returns
        -------
        >>> status   : bool              # Login status
        >>> response : requests.Response # Response from the server
        """
        url = re.search("https://[a-z:0-9.]*/", response.url)
        if url is None:
            self.__console.error("Cound not find base URL via regex match. Exiting")
            exit(code=1)
        url = url[0]
        magic = re.search('(name="magic" value=")([a-zA-Z0-9]+)(")', response.text)
        if magic is None:
            self.__console.error("Could not find magic value via regex match. Exiting")
            exit(code=1)
        magic = magic[2]

        data = {
            "username": self.__parser.username,
            "password": self.__parser.password,
            "magic": magic,
            "4Tredir": "/",
        }

        # Trying to log onto the network
        try:
            response = requests.post(
                url=url, headers={"User-Agent": "Mozilla/5.0"}, data=data
            )
        except requests.exceptions.RequestException:
            self.__console.error(f"Cannot open URL: {url}")
            return False, None
        if response.status_code != 200:
            return False, response

        # If no JS redirect is given, username/password is probably incorrect
        url = re.search(r'window.location="(.*)"', response.text)
        if url is None:
            self.__console.error("Invalid username/password combination. Exiting")
            exit(code=1)
        url = url[1]
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            self.__console.error("Failed to fetch keepalive webpage")
            return False, response

        self.__console.log("Successfully logged in")
        self.__logged_in = True
        self.__logout_url = url.replace("keepalive", "logout")
        return True, response

    def __keepalive(self, url: str) -> None:
        """Keepalive requests

        Parameters
        ----------
        >>> url : str # URL to send keepalive requests to

        Returns
        -------
        >>> None
        """
        while True:
            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            except requests.exceptions.RequestException:
                self.__console.error(f"Cannot open URL: {url}")
                self.__logged_in = False
                break

            # Make sure no redirects occur
            if response.status_code == 200 and response.url == url:
                self.__console.log(f"Keeping alive ({self.__parser.keepalive} seconds)")
                time.sleep(self.__parser.keepalive)
                continue
            else:
                self.__console.error("Something went wrong")
                self.__logged_in = False
                break

    def run(self) -> None:
        """Run the authenticator

        Parameters
        ----------
        >>> None

        Returns
        -------
        >>> None
        """
        while True:
            status, response = self.__state_check()

            # If already logged in, wait for a while before retrying
            if status:
                self.__console.log(
                    f"Already logged in. Sleeping for {self.__parser.retry}"
                )
                time.sleep(self.__parser.retry)
                continue

            # If not logged in, try to log in. Redirection is handled via JS so extract the redirected URL
            url: str = re.search(r'window.location="(.*)"', response.text)[1]
            self.__console.log("Not logged in")
            response = requests.get(url=url, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code != 200:
                self.__console.error("Failed to fetch captive portal webpage. Retrying")
                continue
            status, response = self.__login(response=response)

            # If the log in was unsuccessful, retry
            if not status:
                continue

            # Send keepalive requests
            self.__keepalive(response.url)


if __name__ == "__main__":
    auth = Authenticator()
    auth.run()
