#!/usr/bin/env python3
# -*- coding: latin-1 -*- ######################################################
#                                                                              #
# wordlistctl - Fetch, install and search wordlist archives from websites.     #
#                                                                              #
# DESCRIPTION                                                                  #
# Script to fetch, install, update and search wordlist archives from websites  #
# offering wordlists with more than 6400 wordlists available.                  #
#                                                                              #
# AUTHORS                                                                      #
# sepehrdad@blackarch.org                                                      
# sablea2020@gmail.com                                                         
################################################################################

__all__ = [ "ArgumentParser" ]


import os
import sys
import argparse
import textwrap
import gzip
import tarfile
import time
import json
from shutil import copyfileobj
from concurrent.futures import ThreadPoolExecutor

try:
    import requests
    from termcolor import colored
except Exception as ex:
    print(f"[-] {ex}", file=sys.stderr)
    sys.exit(-1)


# Internal Variables
__organization__: str = "blackarch.org"
__license__: str = "GPLv3"
__version__: str = "v0.9.0"
__project__: str = "wordlistctl"
__description__: str = "Fetch, install and search wordlist archives from websites."


WORDLIST_PATH: str = "/usr/share/wordlists"
REPOSITORY: dict = {}
RETRY_COUNT: int = 5


def error(string: str) -> None:
    print(colored("[-]", "red", attrs=["bold"]) +
          f" {string}", file=sys.stderr)


def warning(string: str) -> None:
    print(colored("[!]", "yellow", attrs=["bold"]) + f" {string}")


def info(string: str) -> None:
    print(colored("[*]", "blue", attrs=["bold"]) + f" {string}")


def success(string: str) -> None:
    print(colored("[+]", "green", attrs=["bold"]) + f" {string}")


def banner() -> None:
    print(colored(f"--==[ {__project__} by {__organization__} ]==--\n",
                  "red", attrs=["bold"]))


def load_repo() -> None:
    global REPOSITORY
    repofile: str = f"{os.path.dirname(os.path.realpath(__file__))}/repo.json"
    try:
        if not os.path.isfile(repofile):
            raise FileNotFoundError("repository file not found")
        REPOSITORY = json.load(open(repofile, 'r'))
    except Exception as ex:
        error(f"Error while loading repository: {str(ex)}")
        exit(-1)


def to_readable_size(size: int) -> str:
    units: dict = {0: 'B',
                   1: 'Kb',
                   2: 'Mb',
                   3: 'Gb',
                   4: 'Tb'}
    i: int = 0
    while size > 1000:
        size = size / 1000
        i += 1
    return f"{size:.2f} {units[i]}"


def decompress_file(infilename: str) -> None:
    filename: str = os.path.basename(infilename).lower()
    try:
        info(f"decompressing {infilename}")
        if filename.endswith(".tar.gz"):
            tar: tarfile.TarFile = tarfile.open(infilename)
            tar.extractall(os.path.dirname(infilename))
        elif filename.endswith(".gz"):
            gf: gzip.GzipFile = gzip.GzipFile(infilename)
            outfile = open(infilename.split(".gz")[0], "wb")
            copyfileobj(gf, outfile)
            outfile.close()
        else:
            warning(f"decompressing {infilename.split('.')[-1]} file type not supported")
            return
        success(f"decompressing {filename} completed")
        os.remove(infilename)
    except Exception as ex:
        error(f"Unable to decompress {infilename}: {ex}")


def fetch_file(url: str, path: str, useragent: str, decompress: bool) -> None:
    filename: str = os.path.basename(path)
    partpath: str = f'{path}.part'
    headers = {"User-Agent": useragent}
    try:
        if os.path.isfile(path):
            warning(f"{filename} already exists -- skipping")
        else:
            if os.path.isfile(partpath):
                info(f"resume downloading {filename} to {partpath}")
                size: int = os.stat(partpath).st_size
                headers["Range"] = f'bytes={size}-'
            else:
                info(f"downloading {filename} to {partpath}")
            for _ in range(RETRY_COUNT):
                rq: requests.Response = requests.get(url, stream=True, headers=headers)
                if rq.status_code == 404:
                    raise FileNotFoundError("host returned 404")
                elif rq.status_code not in [200, 206]:
                    time.sleep(5)
                    continue
                mode: str = "ab" if rq.status_code == 206 else "wb"
                with open(partpath, mode) as fp:
                    for data in rq.iter_content(chunk_size=1024):
                        fp.write(data)
                os.rename(partpath, path)
                success(f"downloading {filename} completed")
                break
        if decompress:
            decompress_file(path)
    except KeyboardInterrupt:
        return
    except Exception as ex:
        error(f"Error while downloading {filename}: {ex}")


def check_dir(dir_name: str) -> None:
    try:
        if os.path.isdir(dir_name) is False:
            info(f"creating directory {dir_name}")
            os.mkdir(dir_name)
    except Exception as ex:
        error(f"unable to create directory: {str(ex)}")
        exit(-1)


def fetch_func(parser: argparse.ArgumentParser) -> None:
    global REPOSITORY

    if parser.wordlist is None and parser.group is None:
        error("no wordlist specified")
        return

    if parser.workers > 25:
        warning("Number of workers is too big, you might get banned.")

    executer: ThreadPoolExecutor = ThreadPoolExecutor(parser.workers)

    check_dir(parser.basedir)

    for group in ["usernames", "passwords",
                  "discovery", "fuzzing", "misc"]:
        check_dir(f"{parser.basedir}/{group}")

    wordlists: list = []

    if parser.wordlist is not None:
        wordlists = [wordlist for wordlist in parser.wordlist]

    if parser.group is not None:
        for wordlist in REPOSITORY:
            if REPOSITORY[wordlist]["group"] in parser.group:
                wordlists.append(wordlist)

    for wordlist in wordlists:
        if wordlist not in REPOSITORY:
            error(f"wordlist not found: {wordlist}")
            continue
        group: str = REPOSITORY[wordlist]["group"]
        filename: str = REPOSITORY[wordlist]["url"].split('/')[-1]
        path: str = f"{parser.basedir}/{group}/{filename}"
        executer.submit(fetch_file, REPOSITORY[wordlist]["url"], path,
                        parser.useragent, parser.decompress)

    executer.shutdown(wait=True)


def search_func(parser: argparse.ArgumentParser) -> None:
    global REPOSITORY

    count: int = 0
    search_term: str = parser.search_term
    try:
        if parser.local:
            for root, _, files in os.walk(parser.basedir):
                for f in files:
                    if f.__contains__(search_term):
                        wordlist = os.path.join(root, f)
                        size = to_readable_size(os.path.getsize(wordlist))
                        print(f"    > {wordlist} ({size})")
                        count += 1
        else:
            for wordlist in REPOSITORY:
                if wordlist.__contains__(search_term):
                    size = REPOSITORY[wordlist]["size"]
                    print(f"    > {wordlist} ({size})")
                    count += 1

        if count == 0:
            error("no wordlists found")
    except Exception as ex:
        error(ex)


def lst_func(parser: argparse.ArgumentParser) -> None:
    global REPOSITORY

    success("available wordlists:")

    print()

    for wordlist in REPOSITORY:
        if parser.group is not None:
            if REPOSITORY[wordlist]["group"] not in parser.group:
                continue
        size: str = REPOSITORY[wordlist]["size"]
        print(f"    > {wordlist} ({size})")

    print()

class ArgumentParser(argparse.ArgumentParser):
	def __init__(self, *args, width=78, **kwargs):
		self.program = { key: kwargs[key] for key in kwargs }
		self.positionals = []
		self.options = []
		self.width = width
		super(ArgumentParser, self).__init__(*args, **kwargs)

	def add_argument(self, *args, **kwargs):
		super(ArgumentParser, self).add_argument(*args, **kwargs)
		argument = { key: kwargs[key] for key in kwargs }

		if (len(args) == 0 or (len(args) == 1 and isinstance(args[0], str) and not args[0].startswith("-"))):
			argument["name"] = args[0] if (len(args) > 0) else argument["dest"]
			self.positionals.append(argument)
			return

		argument["flags"] = [ item for item in args ]
		self.options.append(argument)

	def format_usage(self):

		# Use user-defined usage message
		if ("usage" in self.program):
			prefix = "Usage: "
			wrapper = textwrap.TextWrapper(width=self.width)
			wrapper.initial_indent = prefix
			wrapper.subsequent_indent = len(prefix) * " "
			if (self.program["usage"] == "" or str.isspace(self.program["usage"])):
				return wrapper.fill("No usage information available")
			return wrapper.fill(self.program["usage"])

		# Generate usage message from known arguments
		output = []

		# Determine what to display left and right, determine string length for left
		# and right
		left1 = "Usage: "
		left2 = self.program["prog"] if ("prog" in self.program and self.program["prog"] != "" and not str.isspace(self.program["prog"])) else os.path.basename(sys.argv[0]) if (len(sys.argv[0]) > 0 and sys.argv[0] != "" and not str.isspace(sys.argv[0])) else "script.py"
		llen = len(left1) + len(left2)
		arglist = []
		for option in self.options:
			flags = str.join("|", option["flags"])
			arglist += [ "[%s]" % flags if ("action" in option and (option["action"] == "store_true" or option["action"] == "store_false")) else "[%s %s]" % (flags, option["metavar"]) if ("metavar" in option) else "[%s %s]" % (flags, option["dest"].upper()) if ("dest" in option) else "[%s]" % flags ]
		for positional in self.positionals:
			arglist += [ "%s" % positional["metavar"] if ("metavar" in positional) else "%s" % positional["name"] ]
		right = str.join(" ", arglist)
		rlen = len(right)

		lwidth = llen
		rwidth = max(0, self.width - lwidth - 1)
		if (lwidth > int(self.width / 2) - 1):
			lwidth = max(0, int(self.width / 2) - 1)
			rwidth = int(self.width / 2)
		outtmp = "%-" + str(lwidth) + "s %s"

		# Wrap text for left and right parts, split into separate lines
		wrapper = textwrap.TextWrapper(width=lwidth)
		wrapper.initial_indent = left1
		wrapper.subsequent_indent = len(left1) * " "
		left = wrapper.wrap(left2)
		wrapper = textwrap.TextWrapper(width=rwidth)
		right = wrapper.wrap(right)

		# Add usage message to output
		for i in range(0, max(len(left), len(right))):
			left_ = left[i] if (i < len(left)) else ""
			right_ = right[i] if (i < len(right)) else ""
			output.append(outtmp % (left_, right_))

		# Return output as single string
		return str.join("\n", output)

	def format_help(self):
		output = []
		dewrapper = textwrap.TextWrapper(width=self.width)

		# Add usage message to output
		output.append(self.format_usage())

		# Add description to output if present
		if ("description" in self.program and self.program["description"] != "" and not str.isspace(self.program["description"])):
			output.append("")
			output.append(dewrapper.fill(self.program["description"]))

		lmaxlen = rmaxlen = 0
		for positional in self.positionals:
			positional["left"] = positional["metavar"] if ("metavar" in positional) else positional["name"]
		for option in self.options:
			if ("action" in option and (option["action"] == "store_true" or option["action"] == "store_false")):
				option["left"] = str.join(", ", option["flags"])
			else:
				option["left"] = str.join(", ", [ "%s %s" % (item, option["metavar"]) if ("metavar" in option) else "%s %s" % (item, option["dest"].upper()) if ("dest" in option) else item for item in option["flags"] ])
		for argument in self.positionals + self.options:
			if ("help" in argument and argument["help"] != "" and not str.isspace(argument["help"]) and "default" in argument and argument["default"] != argparse.SUPPRESS):
				argument["right"] = argument["help"] + " " + ( "(default: '%s')" % argument["default"] if isinstance(argument["default"], str) else "(default: %s)" % str(argument["default"]) )
			elif ("help" in argument and argument["help"] != "" and not str.isspace(argument["help"])):
				argument["right"] = argument["help"]
			elif ("default" in argument and argument["default"] != argparse.SUPPRESS):
				argument["right"] = "Default: '%s'" % argument["default"] if isinstance(argument["default"], str) else "Default: %s" % str(argument["default"])
			else:
				argument["right"] = "No description available"
			lmaxlen = max(lmaxlen, len(argument["left"]))
			rmaxlen = max(rmaxlen, len(argument["right"]))

		lwidth = lmaxlen
		rwidth = max(0, self.width - lwidth - 4)
		if (lwidth > int(self.width / 2) - 4):
			lwidth = max(0, int(self.width / 2) - 4)
			rwidth = int(self.width / 2)
		outtmp = "  %-" + str(lwidth) + "s  %s"

		lwrapper = textwrap.TextWrapper(width=lwidth)
		rwrapper = textwrap.TextWrapper(width=rwidth)
		for argument in self.positionals + self.options:
			argument["left"] = lwrapper.wrap(argument["left"])
			argument["right"] = rwrapper.wrap(argument["right"])


		if (len(self.positionals) > 0):
			output.append("")
			output.append("Positionals:")
			for positional in self.positionals:
				for i in range(0, max(len(positional["left"]), len(positional["right"]))):
					left = positional["left"][i] if (i < len(positional["left"])) else ""
					right = positional["right"][i] if (i < len(positional["right"])) else ""
					output.append(outtmp % (left, right))


		if (len(self.options) > 0):
			output.append("")
			output.append("Options:")
			for option in self.options:
				for i in range(0, max(len(option["left"]), len(option["right"]))):
					left = option["left"][i] if (i < len(option["left"])) else ""
					right = option["right"][i] if (i < len(option["right"])) else ""
					output.append(outtmp % (left, right))

		if ("epilog" in self.program and self.program["epilog"] != "" and not str.isspace(self.program["epilog"])):
			output.append("")
			output.append(dewrapper.fill(self.program["epilog"]))

		# Return output as single string
		return str.join("\n", output)

	
	def print_usage(self, file=None):
		if (file == None):
			file = sys.stdout
		file.write(self.format_usage() + "\n")
		file.flush()

	
	def print_help(self, file=None):
		if (file == None):
			file = sys.stdout
		file.write(self.format_help() + "\n")
		file.flush()

	def error(self, message):
		sys.stderr.write(self.format_usage() + "\n")
		sys.stderr.write(("Error: %s" % message) + "\n")
		sys.exit(2)


def main() -> int:
	banner()

	load_repo()

	parser = ArgumentParser(prog=f"{__project__}", description=f"{__description__}", argument_default=argparse.SUPPRESS, allow_abbrev=False, add_help=False)

	# Add options
	parser.add_argument("-v", "--version", action="version", type=str, 
						version=f"{__project__} {__version__}")
	parser.add_argument("-h", "--help", action="help", help="Display this message")

	subparsers = parser.add_subparsers()

	fetch = subparsers.add_parser("fetch", help="fetch wordlists")
	fetch.add_argument("-l", "--wordlist", nargs="+", dest="wordlist",
						help="Wordlist(s) to fetch")
	fetch.add_argument("-d", "--decompress", action="store_true",
                       help="decompress and remove archive")
    fetch.add_argument("-w", "--workers", type=int, default=10,
                       help="download workers [default: %(default)s]")
    fetch.add_argument("-u", "--useragent", default=f"{__project__}/{__version__}",
                       help="fetch user agent [default: %(default)s]")
    fetch.add_argument("-b", "--base-dir", default=f"{WORDLIST_PATH}", dest="basedir",
                       help="wordlists base directory [default: %(default)s]")

	fetch.set_defaults(func=fetch_func)

	search = subparsers.add_parser("search", help="search wordlists")
    search.add_argument("search_term", help="what to search")
    search.add_argument("-l", "--local", action="store_true", default=False,
                        help="search local archives")
    search.add_argument("-b", "--base-dir", default=f"{WORDLIST_PATH}", dest="basedir",
                        help="wordlists base directory [default: %(default)s]")
    search.set_defaults(func=search_func)

    lst = subparsers.add_parser("list", help="list wordlists")
    lst.add_argument("-g", "--group",
                     choices=["usernames", "passwords",
                              "discovery", "fuzzing", "misc"],
                     help="group")
    lst.set_defaults(func=lst_func)

	# Parse command line
	results = parser.parse_args()
	if sys.argv.__len__() == 1:
		parser.print_help()
		return

	try:
		results.func(results)
	except Exception as ex:
		error(f"Error while parsing arguments: {ex}")

if __name__ == "__main__":
	sys.exit(main())
