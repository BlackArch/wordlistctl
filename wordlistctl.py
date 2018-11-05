#!/usr/bin/env python3

__author__ = 'Sepehrdad Sh'
__organization__ = 'blackarch.org'
__license__ = 'GPLv3'
__version__ = '0.2alpha'
__project__ = 'wordlistctl.py'

__wordlist_path__ = '/usr/share/wordlists'
__urls_file_name__ = ''
__categories_file_name__ = ''
__urls__ = {}
__categories__ = {}
__decompress__ = False
__remove__ = False


def printerr(string, ex):
    if ex == '':
        print("[-] {0}".format(string), file=sys.stderr)
    else:
        print("[-] {0}: {1}".format(string, ex), file=sys.stderr)


def usage():
    __usage__ = "usage:\n"
    __usage__ += "  {0} -f <num>  [options] | -s <arg> | -S <arg> | <misc>\n\n"
    __usage__ += "options:\n\n"
    __usage__ += "  -f <num>   - download chosen wordlist\n"
    __usage__ += "             - ? to list wordlists\n"
    __usage__ += "             - h to show options\n"
    __usage__ += "  -d <dir>   - wordlists base directory (default: {1})\n"
    __usage__ += "  -s <regex> - wordlist to search using <regex> in base directory\n"
    __usage__ += "  -S <str>   - wordlist to search using str in sites\n\n"
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
        if input.endswith('.gz'):
            infile = gzip.GzipFile(input, 'rb')
        elif input.endswith('.bz2'):
            infile = bz2.BZ2File(input, 'rb')
        elif input.endswith('.lzma') or input.endswith('.xz'):
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
        if os.path.splitext(__filename__)[1] in '.rar':
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

        if os.path.splitext(__filename__)[1] in ('.zip', '.rar', '.7z', '.tar'):
            return decompress_archive(input, output)
        elif os.path.splitext(__filename__)[1] in ('.gz', '.bz', '.bz2', '.xz', '.lzma'):
            if os.path.splitext(__filename__)[0].endswith('.tar'):
                return decompress_archive(input, output)
            return decompress_gbl(input, output)
        else:
            raise ValueError('unknown file type')
    except Exception as ex:

        printerr('Error while decompressing {0}'.format(__infile__.split('/')[-1]), ex)
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
            print('[*] downloading metadata')
            while not handle.has_metadata():
                time.sleep(1)
            print('[+] downloaded metadata')
        else:
            if os.path.isfile(url):
                handle = session.add_torrent({'ti': libtorrent.torrent_info(url), 'save_path': path})
            else:
                printerr("[-] {0} not found".format(url), '')
                exit(-1)

        print("[*] downloading {0}".format(handle.name()))

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
        printerr('{0} is not a valid option'.format(code), '')
        return -1

    try:

        if (__wordlist_id__ >= __urls__.__len__() + 1) or __wordlist_id__ < 0:
            raise IndexError('{0} is not a valid option'.format(code))
        elif __wordlist_id__ == 0:
            for i in __urls__:
                download_wordlist(__urls__[i])
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
    for i in __urls__:
        print("    > {0}  - {1}".format(index, i))
        index += 1


def search_dir(regex):
    print('[*] searching for {0} in {1}'.format(regex, __wordlist_path__))
    os.chdir(__wordlist_path__)
    files = glob.glob("{0}".format(str(regex)))
    if files.__len__() <= 0:
        print("[-] wordlist not found")
        return
    for file in files:
        print("[+] wordlist found: {0}".format(os.path.join(__wordlist_path__, file)))


def search_weakpass(string):
    try:
        __items__ = {}
        print('[*] searching for {0} in weakpass.com'.format(string))
        page = requests.get('https://weakpass.com/wordlist')
        html = BeautifulSoup(page.text, 'html.parser')
        tbody = html.tbody
        for i in tbody.find_all('tr'):
            __items__[i.find_all('td')[0].a.text] = i.find_all('td')[5].a['href']

        for i in __items__.keys():
            if i.lower().__contains__(string):
                print('[+] wordlist {0} found: https://weakpass.com{1}'.format(i, __items__[i]))
    except KeyboardInterrupt:
        pass
    except Exception as ex:

        printerr('Error while searching', ex)
        return -1


def search_sites(string):
    try:
        print('[*] searching for {0} in urls.json'.format(string))
        count = 0
        for i in __urls__.keys():
            if i.lower().__contains__(string):
                print('[+] wordlist {0} found: {1}'.format(i, __urls__[i]['url']))
                count += 1

        if count == 0:
            search_weakpass(string)
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
            print("[*] creating directory {0}".format(dir_name))
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


def arg_parse(argv):
    global __wordlist_path__
    global __decompress__
    global __remove__
    __operation__ = None
    __arg__ = None

    try:
        opts, args = getopt.getopt(argv[1:], "hvXUrd:f:s:S:")

        if opts.__len__() <= 0:
            __operation__ = usage
            return __operation__, __arg__

        for opt, arg in opts:
            if opt == '-h':
                __operation__ = usage
            elif opt == '-v':
                __operation__ = version
            elif opt == '-d':
                check_dir(arg)
                __wordlist_path__ = arg
            elif opt == '-f':
                if arg == '?':
                    __operation__ = print_wordlists
                elif arg == 'h':
                    __usage__ = "options:\n\n"
                    __usage__ += "  -X         - decompress wordlist\n"
                    __usage__ += "  -r         - remove compressed file after decompression\n"
                    print(__usage__)
                else:
                    __operation__ = download_wordlists
                    __arg__ = arg
            elif opt == '-s':
                __operation__ = search_dir
                __arg__ = arg
            elif opt == '-X':
                __decompress__ = True
            elif opt == '-r':
                __remove__ = True
            elif opt == '-U':
                __operation__ = update_config
            elif opt == '-S':
                __operation__ = search_sites
                __arg__ = arg
    except Exception as ex:

        printerr("Error while parsing arguments", ex)
    finally:
        return __operation__, __arg__


def update_config():
    global __urls__
    global __categories__
    __base_url__ = 'https://raw.githubusercontent.com/BlackArch/wordlistctl/master'
    files = [__urls_file_name__, __categories_file_name__]
    try:

        print('[*] updating config files')
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
    try:

        for i in files:
            if not os.path.isfile(i):
                raise FileNotFoundError('Config files not found please update')
        __urls__ = load_json(__urls_file_name__)
        __categories__ = load_json(__categories_file_name__)
    except Exception as ex:

        printerr('Error while loading config files', ex)
        exit(-1)


def main(argv):
    global __urls_file_name__
    global __categories_file_name__
    banner()
    __base_name__ = os.path.dirname(os.path.realpath(__file__))
    __urls_file_name__ = '{0}/urls.json'.format(__base_name__)
    __categories_file_name__ = '{0}/categories.json'.format(__base_name__)

    __operation__, __arg__ = arg_parse(argv)

    try:
        if __operation__ is not update_config:
            load_config()
        if __operation__ is not None:
            if __arg__ is not None:
                __operation__(__arg__)
            else:
                __operation__()
        else:
            raise ValueError
        return 0
    except:
        return -1


if __name__ == '__main__':
    try:

        import sys
        import os
        import getopt
        import requests
        import glob
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
