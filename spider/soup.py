#!/usr/bin/env python

import urllib2

from bs4 import BeautifulSoup


def get_content(filepath):
    if filepath.startswith('http'):
        content = urllib2.urlopen(filepath).read()
    else:
        content = open(filepath).read()
    return content

def main(filepath):
    content = get_content(filepath)
    soup = BeautifulSoup(content)

    urls = []

    for elem in soup.find_all('a'):
        url = elem.get('href')
        urls.append(url)

    for elem in soup.find_all('link'):
        url = elem.get('href')
        urls.append(url)

    for elem in soup.find_all('script'):
        url = elem.get('src')
        urls.append(url)

    for elem in soup.find_all('img'):
        url = elem.get('src')
        urls.append(url)

    for elem in soup.find_all('iframe'):
        url = elem.get('src')
        urls.append(url)

    display(urls)

def display(urls):
    urls = list(set(urls))
    for url in sorted(urls):
        print(url)


if __name__ == '__main__':
    import sys
    main(sys.argv[1])
