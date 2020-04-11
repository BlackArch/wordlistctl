#!/usr/bin/env python3
# -*- coding: latin-1 -*- ######################################################
#                                                                              #
# wordlistctl - Fetch, install and search wordlist archives from websites.     #
#                                                                              #
# DESCRIPTION                                                                  #
# Script to fetch, install, update and search wordlist archives from websites  #
# offering wordlists with more than 6300 wordlists available.                  #
#                                                                              #
# AUTHORS                                                                      #
# sepehrdad@blackarch.org                                                      #
################################################################################


# Internal Variables
__organization__ = "blackarch.org"
__license__ = "GPLv3"
__version__ = "v0.8.8-dev"
__project__ = "wordlistctl"
__description__ = "Fetch, install and search wordlist archives from websites."


wordlist_path = "/usr/share/wordlists"
repo = {}
retry_count = 5


def error(string):
    print(colored("[-]", "red", attrs=["bold"]) +
          f" {string}", file=sys.stderr)


def warning(string):
    print(colored("[!]", "yellow", attrs=["bold"]) + f" {string}")


def info(string):
    print(colored("[*]", "blue", attrs=["bold"]) + f" {string}")


def success(string):
    print(colored("[+]", "green", attrs=["bold"]) + f" {string}")


def banner():
    print(colored(f"--==[ {__project__} by {__organization__} ]==--\n",
                  "red", attrs=["bold"]))


def load_repo():
    global repo
    repofile = f"{os.path.dirname(os.path.realpath(__file__))}/repo.json"
    try:
        if not os.path.isfile(repofile):
            raise FileNotFoundError("repository file not found")
        repo = json.load(open(repofile, 'r'))
    except Exception as ex:
        error(f"Error while loading repository: {str(ex)}")
        exit(-1)


def to_readable_size(size):
    units = {0: 'B',
             1: 'Kb',
             2: 'Mb',
             3: 'Gb',
             4: 'Tb'}
    i = 0
    while size > 1000:
        size = size / 1000
        i += 1
    return f"{size:.2f} {units[i]}"


def decompress_file(infilename):
    filename = os.path.basename(infilename).lower()
    try:
        if filename.endswith(".tar.gz"):
            tar = tarfile.open(infilename)
            tar.extractall(os.path.dirname(infilename))
        elif filename.endswith(".gz"):
            gf = gzip.GzipFile(infilename)
            outfile = open(infilename.split(".gz")[0], "wb")
            copyfileobj(gf, outfile)
            outfile.close()
        else:
            return
        os.remove(infilename)
    except Exception as ex:
        error(f"Unable to decompress file: {ex}")


def fetch_file(url, path, useragent, decompress):
    filename = os.path.basename(path)
    try:
        if os.path.isfile(path):
            warning(f"{filename} already exists -- skipping")
        else:
            info(f"downloading {filename} to {path}")
            for retry in range(retry_count):
                rq = requests.get(url, stream=True,
                                headers={"User-Agent": useragent})
                if rq.status_code == 404:
                    raise FileNotFoundError("host returned 404")
                elif rq.status_code != 200:
                    time.sleep(5)
                    continue
                fp = open(path, "wb")
                for data in rq.iter_content(chunk_size=1024):
                    fp.write(data)
                fp.close()
                success(f"downloading {filename} completed")
                break
        if decompress:
            decompress_file(path)
    except KeyboardInterrupt:
        return
    except Exception as ex:
        error(f"Error while downloading {filename}: {ex}")


def check_dir(dir_name):
    try:
        if os.path.isdir(dir_name) is False:
            info(f"creating directory {dir_name}")
            os.mkdir(dir_name)
    except Exception as ex:
        error(f"unable to create directory: {str(ex)}")
        exit(-1)


def fetch_func(parser):
    if parser.wordlist is None and parser.group is None:
        error("no wordlist specified")
        return

    executer = ThreadPoolExecutor(parser.workers)

    check_dir(parser.basedir)

    for group in ["usernames", "passwords",
                  "discovery", "fuzzing", "misc"]:
        check_dir(f"{parser.basedir}/{group}")

    wordlists = []

    if parser.wordlist is not None:
        wordlists = [wordlist for wordlist in parser.wordlist]

    if parser.group is not None:
        for wordlist in repo:
            if repo[wordlist]["group"] in parser.group:
                wordlists.append(wordlist)

    for wordlist in wordlists:
        group = repo[wordlist]["group"]
        filename = repo[wordlist]["url"].split('/')[-1]
        path = f"{parser.basedir}/{group}/{filename}"
        executer.submit(fetch_file, repo[wordlist]["url"], path,
                        parser.useragent, parser.decompress)


    executer.shutdown(wait=True)

def search_func(parser):
    count = 0
    search_term = parser.search_term
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
            for wordlist in repo:
                if wordlist.__contains__(search_term):
                    size = repo[wordlist]["size"]
                    print(f"    > {wordlist} ({size})")
                    count += 1

        if count == 0:
            error("no wordlists found")
    except Exception as ex:
        error(ex)


def lst_func(parser):
    success("available wordlists:")

    print()

    for wordlist in repo:
        if parser.group is not None:
            if repo[wordlist]["group"] not in parser.group:
                continue
        size = repo[wordlist]["size"]
        print(f"    > {wordlist} ({size})")

    print()


def main():
    banner()

    load_repo()

    parser = argparse.ArgumentParser(prog=f"{__project__}",
                                     description=f"{__description__}")
    parser.add_argument("-v", "--version", action="version",
                        version=f"{__project__} {__version__}")

    subparsers = parser.add_subparsers()

    fetch = subparsers.add_parser("fetch", help="fetch wordlists")
    fetch.add_argument("-l", "--wordlist", nargs='+', dest="wordlist",
                       help="wordlist to fetch")
    fetch.add_argument("-g", "--group", nargs='+', dest="group",
                       choices=["usernames", "passwords",
                                "discovery", "fuzzing", "misc"],
                       help="wordlist group to fetch")
    fetch.add_argument("-d", "--decompress", action="store_true",
                       help="decompress and remove archive")
    fetch.add_argument("-w", "--workers", type=int, default=10,
                       help="download workers [default: %(default)s]")
    fetch.add_argument("-u", "--useragent", default=f"{__project__}/{__version__}",
                       help="fetch user agent [default: %(default)s]")
    fetch.add_argument("-b", "--base-dir", default=f"{wordlist_path}", dest="basedir",
                       help="wordlists base directory [default: %(default)s]")

    fetch.set_defaults(func=fetch_func)

    search = subparsers.add_parser("search", help="search wordlists")
    search.add_argument("search_term", help="what to search")
    search.add_argument("-l", "--local", action="store_true", default=False,
                        help="search local archives")
    search.add_argument("-b", "--base-dir", default=f"{wordlist_path}", dest="basedir",
                        help="wordlists base directory [default: %(default)s]")
    search.set_defaults(func=search_func)

    lst = subparsers.add_parser("list", help="list wordlists")
    lst.add_argument("-g", "--group",
                     choices=["usernames", "passwords",
                              "discovery", "fuzzing", "misc"],
                     help="group")
    lst.set_defaults(func=lst_func)

    results = parser.parse_args()

    if sys.argv.__len__() == 1:
        parser.print_help()
        return

    try:
        results.func(results)
    except Exception as ex:
        error(ex)


if __name__ == "__main__":
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
    sys.exit(main())
