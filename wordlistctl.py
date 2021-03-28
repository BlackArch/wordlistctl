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
# sepehrdad@blackarch.org                                                      #
################################################################################


import argparse
import gzip
import tarfile
import time
import json
import os
import sys
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
SEARCH_RESULTS: list = []


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
    global SEARCH_RESULTS

    SEARCH_RESULTS = []

    count: int = 0
    search_term: str = parser.search_term
    search_results: list = []
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
                    print(f"    {count} > {wordlist} ({size})")
                    count += 1
                    SEARCH_RESULTS.append(wordlist)

        if count == 0:
            error("no wordlists found")
    except Exception as ex:
        error(ex)


def lst_func(parser: argparse.ArgumentParser) -> None:
    global REPOSITORY
    global SEARCH_RESULTS

    SEARCH_RESULTS = []

    success("available wordlists:")

    print()

    count: int = 0
    for wordlist in REPOSITORY:
        if parser.group is not None:
            if REPOSITORY[wordlist]["group"] not in parser.group:
                continue
        size: str = REPOSITORY[wordlist]["size"]
        print(f"   {count} > {wordlist} ({size})")
        SEARCH_RESULTS.append(wordlist)
        count += 1

    print()


def add_fetch_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-d", "--decompress", action="store_true",
                       help="decompress and remove archive")
    parser.add_argument("-w", "--workers", type=int, default=10,
                       help="download workers [default: %(default)s]")
    parser.add_argument("-u", "--useragent", default=f"{__project__}/{__version__}",
                       help="parser user agent [default: %(default)s]")


def main() -> int:
    banner()

    load_repo()

    parser = argparse.ArgumentParser(prog=f"{__project__}",
                                     description=f"{__description__}")
    parser.add_argument("-v", "--version", action="version",
                        version=f"{__project__} {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    fetch = subparsers.add_parser("fetch", help="fetch wordlists")
    fetch.add_argument("-l", "--wordlist", nargs='+', dest="wordlist",
                       help="wordlist to fetch")
    fetch.add_argument("-g", "--group", nargs='+', dest="group",
                       choices=["usernames", "passwords",
                                "discovery", "fuzzing", "misc"],
                       help="wordlist group to fetch")
    fetch.add_argument("-b", "--base-dir", default=f"{WORDLIST_PATH}", dest="basedir",
                       help="wordlists base directory [default: %(default)s]")

    add_fetch_options(fetch)

    fetch.set_defaults(func=fetch_func)

    search = subparsers.add_parser("search", help="search wordlists")
    search.add_argument("search_term", help="what to search")
    search.add_argument("-l", "--local", action="store_true", default=False,
                        help="search local archives")
    search.add_argument("-b", "--base-dir", default=f"{WORDLIST_PATH}", dest="basedir",
                        help="wordlists base directory [default: %(default)s]")
    search.add_argument("-f", "--fetch", type=int, nargs='+', dest="indexes", metavar="INDEX",
                        help=("fetch the wordlists at the given indexes in the search "
                              "results, see fetch options for additional options"))

    search_fetch = search.add_argument_group("fetch options")
    add_fetch_options(search_fetch)

    search.set_defaults(func=search_func)

    lst = subparsers.add_parser("list", help="list wordlists")
    lst.add_argument("-g", "--group",
                     choices=["usernames", "passwords",
                              "discovery", "fuzzing", "misc"],
                     help="group")
    lst.add_argument("-f", "--fetch", type=int, nargs='+', dest="indexes", metavar="INDEX",
                        help=("fetch the wordlists at the given indexes in the list, "
                              "see fetch options for additiional options"))

    lst_fetch = lst.add_argument_group("fetch options")
    add_fetch_options(lst_fetch)

    lst.set_defaults(func=lst_func)

    results = parser.parse_args()

    if sys.argv.__len__() == 1:
        parser.print_help()
        return

    try:
        results.func(results)
        if results.command != "fetch" and results.indexes is not None:
            setattr(results, "wordlist", [])
            # group argument added so `fetch_func` does not complain
            setattr(results, "group", None)
            for i in results.indexes:
                try:
                    results.wordlist.append(SEARCH_RESULTS[i])
                except IndexError:
                    error(f"no wordlist with index: {i}")
            fetch_func(results)
    except Exception as ex:
        error(f"Error while parsing arguments: {ex}")


if __name__ == "__main__":
    sys.exit(main())
