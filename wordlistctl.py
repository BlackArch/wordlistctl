#!/usr/bin/env python3

__author__ = 'Sepehrdad Sh'
__organization__ = 'blackarch.org'
__license__ = 'GPLv3'
__version__ = '0.2'
__project__ = 'wordlistctl.py'

__wordlist_path__ = '/usr/share/wordlists'
__urls_file_name__ = ''
__categories_file_name__ = ''
__urls__ = {}
__categories__ = {}
__decompress__ = False
__remove__ = False
__category__ = ''


def printerr(string, ex):
    if ex == '':
        print("[-] {0}".format(string), file=sys.stderr)
    else:
        print("[-] {0}: {1}".format(string, ex), file=sys.stderr)


def usage():
    __usage__ = "usage:\n"
    __usage__ += "  {0} -f <arg>  [options] | -s <arg> | -S <arg> | <misc>\n\n"
    __usage__ += "options:\n\n"
    __usage__ += "  -f <num>   - download chosen wordlist\n"
    __usage__ += "             - ? to list wordlists\n"
    __usage__ += "             - h to show options\n"
    __usage__ += "  -d <dir>   - wordlists base directory (default: {1})\n"
    __usage__ += "  -c <num>   - change wordlists category\n"
    __usage__ += "             - ? to list wordlists categories\n"
    __usage__ += "  -s <regex> - wordlist to search using <regex> in base directory\n"
    __usage__ += "  -S <regex> - wordlist to search using <regex> in sites\n\n"
    __usage__ += "misc:\n\n"
    __usage__ += "  -U         - update config files\n"
    __usage__ += "  -v         - print version of wordlistctl and exit\n"
    __usage__ += "  -h         - print this help and exit\n"

    print(__usage__.format(__project__, __wordlist_path__))


def version():
    __str_version__ = "{0} v{1}".format(__project__, __version__)
    print(__str_version__)


def banner():
    __str_banner__ = "--==[ {0} by {1} ]==--\n".format(__project__, __organization__)
    print(__str_banner__)


def decompress_gbl(input, output):
    __filename__ = os.path.basename(input)
    try:

        infile = None
        __outfile__ = os.path.splitext(os.path.basename(input))[0]
        if re.fullmatch(r"^.*\.(gz)$", input.lower()):
            infile = gzip.GzipFile(input, 'rb')
        elif re.fullmatch(r"^.*\.(bz|bz2)$", input.lower()):
            infile = bz2.BZ2File(input, 'rb')
        elif re.fullmatch(r"^.*\.(lzma|xz)$", input.lower()):
            infile = lzma.LZMAFile(input, 'rb')
        else:
            raise ValueError('unknown file type')
        print("[*] decompressing {0}".format(__filename__))
        outfile = open("{0}/{1}".format(output, __outfile__), 'wb')
        copyfileobj(infile, outfile)
        outfile.close()
        print("[+] decompressing {0} completed".format(__filename__))
    except Exception as ex:

        printerr('Error while decompressing {0}'.format(__filename__), ex)
        return -1


def decompress_archive(input, output):
    __filename__ = os.path.basename(input)
    try:

        os.chdir(output)
        print("[*] decompressing {0}".format(__filename__))
        if re.fullmatch(r"^.*\.(rar)$", __filename__.lower()):
            infile = rarfile.RarFile(input)
            infile.extractall()
        else:
            libarchive.extract_file(input)
        print("[+] decompressing {0} completed".format(__filename__))
    except Exception as ex:

        printerr('Error while decompressing {0}'.format(__filename__), ex)
        return -1


def decompress(input, output):
    __infile__ = os.path.abspath(input)
    __filename__ = os.path.basename(__infile__)
    try:

        if re.fullmatch(r"^.*\.(rar|zip|7z|tar|tar.gz|tar.xz)$", __filename__.lower()):
            return decompress_archive(input, output)
        elif re.fullmatch(r"^.*\.(gz|bz|bz2|lzma)$", __filename__.lower()):
            return decompress_gbl(input, output)
        else:
            raise ValueError('unknown file type')
    except Exception as ex:

        printerr('Error while decompressing {0}'.format(__filename__), ex)
        return -1


def resolve_mediafire(link):
    resolved = ''
    try:
        page = requests.get(link)
        html = BeautifulSoup(page.text, 'html.parser')
        for i in html.find_all('a'):
            if str(i.text).startswith('Download ('):
                resolved = i['href']
    except:
        pass
    finally:
        return resolved


def fetch_file(url, path):
    infile = path.split('/')[-1]
    print("[*] downloading {0}".format(infile))
    str_url = url
    try:
        if str(url).startswith('http://www.mediafire.com/file/'):
            str_url = resolve_mediafire(url)
        chunk_size = 1024
        rq = requests.get(str_url, stream=True)
        total_size = int(rq.headers['content-length'])
        fp = open(path, 'wb')
        for data in tqdm(iterable=rq.iter_content(chunk_size=chunk_size), total=total_size / chunk_size, unit='KB'):
            fp.write(data)
        fp.close()
        print("[+] downloading {0} completed".format(infile))
        if __decompress__ and (not infile.endswith('.torrent')):
            if decompress(infile, __wordlist_path__) != -1 and __remove__:
                    os.remove(infile)
    except KeyboardInterrupt:

        return
    except Exception as ex:

        printerr("Error while downloading {0}".format(url), ex)
        os.remove(path)


def fetch_torrent(url, path):
    magnet = False
    if str(url).startswith('magnet:?'):
        magnet = True
    handle = None

    try:

        session = libtorrent.session({'listen_interfaces': '0.0.0.0:6881'})

        if magnet:
            handle = libtorrent.add_magnet_uri(session, url,
                                               {'save_path': path, 'storage_mode': libtorrent.storage_mode_t(2),
                                                'paused': False, 'auto_managed': True, 'duplicate_is_error': True}
                                               )
            session.start_dht()
            print('[*] downloading metadata\n')
            while not handle.has_metadata():
                time.sleep(1)
            print('[+] downloaded metadata')
        else:
            if os.path.isfile(url):
                handle = session.add_torrent({'ti': libtorrent.torrent_info(url), 'save_path': path})
            else:
                printerr("[-] {0} not found".format(url), '')
                exit(-1)

        print("[*] downloading {0}\n".format(handle.name()))

        while not handle.is_seed():
            s = handle.status()
            print('\r  %.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % (
                s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, s.num_peers, s.state), end=' ')
            sys.stdout.flush()
            time.sleep(1)

        print('\n[+] downloading {0} completed'.format(handle.name()))

        if __decompress__:
            if decompress(handle.name(), __wordlist_path__) != -1 and __remove__:
                os.remove(handle.name())
    except KeyboardInterrupt:

        return
    except Exception as ex:

        printerr("Error while downloading {0}".format(url), ex)
        os.remove(path)


def download_wordlist(config):
    try:

        __filename__ = config['url'].split('/')[-1]
        __file_path__ = "{0}/{1}".format(__wordlist_path__, __filename__)
        if config['protocol'] == 'http':
            fetch_file(config['url'], __file_path__)
        elif config['protocol'] == 'torrent':
            fetch_file(config['url'], __file_path__)
            fetch_torrent(__file_path__, __wordlist_path__)
            os.remove(__file_path__)
        elif config['protocol'] == 'magnet':
            fetch_torrent(config['url'], __wordlist_path__)
        else:
            raise ValueError('invalid protocol')
    except Exception as ex:

        printerr('unable to download wordlist', ex)
        return -1


def download_wordlists(code):
    __wordlist_id__ = 0

    check_dir(__wordlist_path__)

    try:
        __wordlist_id__ = int(code)
    except:
        printerr('{0} is not a valid number'.format(code), '')
        return -1

    try:

        if (__wordlist_id__ >= __urls__.__len__() + 1) or __wordlist_id__ < 0:
            raise IndexError('{0} is not a valid wordlist id'.format(code))
        elif __wordlist_id__ == 0:
            if __category__ == '':
                for i in __urls__:
                    download_wordlist(__urls__[i])
            else:
                for i in __categories__[__category__]:
                    download_wordlist(__urls__[i])
        elif __category__ != '':
            i = __urls__[__categories__[__category__][__wordlist_id__ - 1]]
            download_wordlist(i)
        else:
            i = list(__urls__.keys())[__wordlist_id__ - 1]
            download_wordlist(__urls__[i])

    except Exception as ex:

        printerr("Error unable to download wordlist", ex)
        return -1

    return 0


def print_wordlists():
    index = 1
    print("[+] available wordlists")
    print("    > 0  - all wordlists")
    urls = {}
    if __category__ != '':
        urls = __categories__[__category__]
    else:
        urls = __urls__.keys()
    for i in urls:
        print("    > {0}  - {1}".format(index, i))
        index += 1


def search_dir(regex):
    print('[*] searching for {0} in {1}\n'.format(regex, __wordlist_path__))
    os.chdir(__wordlist_path__)
    files = glob.glob("{0}".format(str(regex)))
    if files.__len__() <= 0:
        print("[-] wordlist not found")
        return
    for file in files:
        print("[+] wordlist found: {0}".format(os.path.join(__wordlist_path__, file)))


def search_sites(regex):
    urls = []
    if __category__ != '':
        urls = list(__categories__[__category__])
    else:
        urls = list(__urls__.keys())
    try:
        print('[*] searching for {0} in urls.json\n'.format(regex))
        count = 0
        for i in urls:
            if re.match(regex, i):
                print('[+] wordlist {0} found: id={1}'.format(i, urls.index(i) + 1))
                count += 1

        if count == 0:
            print('[-] no wordlist found')
    except KeyboardInterrupt:
        pass
    except Exception as ex:

        printerr('Error while searching', ex)
        return -1


def check_dir(dir_name):
    try:

        if os.path.isdir(dir_name):
            pass
        else:
            print("[*] creating directory {0}\n".format(dir_name))
            os.mkdir(dir_name)

    except Exception as ex:

        printerr("unable to change base directory", ex)
        exit(-1)


def load_json(input):
    try:

        return json.load(open(input, 'r'))
    except Exception as ex:

        printerr('unable to load {0}'.format(input), ex)
        return {}


def change_category(code):
    global __category__
    global __categories__
    __category_id__ = 0
    if __categories__.__len__() <= 0:
        load_config()

    try:
        __category_id__ = int(code)
    except:
        printerr('{0} is not a valid number'.format(code), '')
        exit(-1)

    try:
        if (__category_id__ >= __categories__.__len__()) or __category_id__ < 0:
            raise IndexError('{0} is not a valid category id'.format(code))
        __category__ = list(__categories__.keys())[__category_id__]
    except Exception as ex:
        printerr('Error while changing category', ex)
        exit(-1)


def print_categories():
    index = 0
    print("[+] available wordlists category")
    for i in __categories__:
        print("    > {0}  - {1} ({2} wordlists)".format(index, i, list(__categories__[i]).__len__()))
        index += 1


def file_usage():
    __usage__ = "options:\n\n"
    __usage__ += "  -X         - decompress wordlist\n"
    __usage__ += "  -r         - remove compressed file after decompression\n"
    print(__usage__)


def update_config():
    global __urls__
    global __categories__
    __base_url__ = 'https://raw.githubusercontent.com/BlackArch/wordlistctl/master'
    files = [__urls_file_name__, __categories_file_name__]
    try:

        print('[*] updating config files\n')
        for i in files:
            if os.path.isfile(i):
                os.remove(i)
            fetch_file('{0}/{1}'.format(__base_url__, os.path.basename(i)), i)
        load_config()
        print('[+] updating config files completed')
    except Exception as ex:

        printerr('Error while updating', ex)
        exit(-1)


def load_config():
    global __urls__
    global __categories__
    files = [__urls_file_name__, __categories_file_name__]
    if __urls__.__len__() <= 0 or __categories__.__len__() <= 0:
        try:

            for i in files:
                if not os.path.isfile(i):
                    raise FileNotFoundError('Config files not found please update')
            __urls__ = load_json(__urls_file_name__)
            __categories__ = load_json(__categories_file_name__)
        except Exception as ex:

            printerr('Error while loading config files', ex)
            exit(-1)


def arg_parse(argv):
    global __wordlist_path__
    global __decompress__
    global __remove__
    __operation__ = None
    __arg__ = None
    opFlag = 0

    try:
        opts, args = getopt.getopt(argv[1:], "hvXUrd:c:f:s:S:")

        if opts.__len__() <= 0:
            __operation__ = usage
            return __operation__, __arg__

        for opt, arg in opts:
            if opFlag and re.fullmatch(r"^-([hvfsSU])", opt):
                raise OverflowError("multiple operations selected")
            if opt == '-h':
                __operation__ = usage
                opFlag += 1
            elif opt == '-v':
                __operation__ = version
                opFlag += 1
            elif opt == '-d':
                dirname = os.path.abspath(arg)
                check_dir(dirname)
                __wordlist_path__ = dirname
            elif opt == '-f':
                if arg == '?':
                    __operation__ = print_wordlists
                elif arg == 'h':
                    __operation__ = file_usage
                else:
                    __operation__ = download_wordlists
                    __arg__ = arg
                opFlag += 1
            elif opt == '-s':
                __operation__ = search_dir
                __arg__ = arg
                opFlag += 1
            elif opt == '-X':
                __decompress__ = True
            elif opt == '-r':
                __remove__ = True
            elif opt == '-U':
                __operation__ = update_config
                opFlag += 1
            elif opt == '-S':
                __operation__ = search_sites
                __arg__ = arg
                opFlag += 1
            elif opt == '-c':
                if arg == '?':
                    if opFlag:
                        raise OverflowError("multiple operations selected")
                    __operation__ = print_categories
                    opFlag += 1
                else:
                    change_category(arg)

    except Exception as ex:

        printerr("Error while parsing arguments", ex)
        exit(-1)
    return __operation__, __arg__


def main(argv):
    global __urls_file_name__
    global __categories_file_name__
    banner()
    __base_name__ = os.path.dirname(os.path.realpath(__file__))
    __urls_file_name__ = '{0}/urls.json'.format(__base_name__)
    __categories_file_name__ = '{0}/categories.json'.format(__base_name__)

    __operation__, __arg__ = arg_parse(argv)

    try:
        if __operation__ not in [update_config, version, usage]:
            load_config()
        if __operation__ is not None:
            if __arg__ is not None:
                __operation__(__arg__)
            else:
                __operation__()
        else:
            raise ValueError("no operation selected")
        return 0
    except Exception as ex:
        printerr("Error while running operation", ex)
        return -1


if __name__ == '__main__':
    try:

        import sys
        import os
        import getopt
        import requests
        import glob
        import re
        from tqdm import tqdm
        import libtorrent
        import libarchive
        import time
        import gzip
        import bz2
        import lzma
        import rarfile
        from shutil import copyfileobj
        import json
        from bs4 import BeautifulSoup

    except Exception as ex:

        printerr("Error while loading dependencies", ex)
        exit(-1)

    sys.exit(main(sys.argv))
