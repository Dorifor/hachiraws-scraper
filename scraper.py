import requests
from bs4 import BeautifulSoup as bs4
import os
from typing import TypedDict, List, Tuple
import time
from logger import log

RAWS_PATH = "./Raws/"
URL = "https://hachiraw.com/manga/ashon-de-yo-uchi-no-inu-log/"
SEARCH_URL = "https://hachiraw.com/search?keyword="
manga_path = ""

class Manga(TypedDict):
    title: str
    author: str
    artist: str
    description: str
    genre: List[str]
    chapters: Tuple[str, str]


def remove_raw_free(string: str) -> str:
    return string.replace("(Raw - Free)", "").strip()

def remove_illegal_characters(string: str) -> str:
    invalid = '<>:"/\|?* '
    for char in invalid:
        string = string.replace(char, '')
    return string


def request_search(query) -> List[Tuple[str, str, str]]:
    page = requests.get(SEARCH_URL + query)
    soup = bs4(page.content, "html.parser")
    manga_list = soup.select(".manga-item .thumb > a")
    manga_list = list(map(lambda manga: (remove_raw_free(manga["title"]), manga['href'], manga.img['data-src']), manga_list))
    log(manga_list)
    return manga_list


def request_chapter_data(url: str) -> List[str]:
    page = requests.get(url)
    soup = bs4(page.content, "html.parser")

    chapter_pages = soup.select("div.chapter-page > img")
    chapter_pages = list(map(lambda page: page['src'], chapter_pages))
    return chapter_pages


def create_folder_structure_and_fill_chapters(manga_data: str) -> None:
    manga_path = RAWS_PATH + remove_illegal_characters(manga_data['title'])
    os.mkdir(manga_path)
    log("Created dir: " + manga_path)
    for chapter in manga_data['chapters']:
        chapter_path = manga_path + "/" + chapter[0]
        os.mkdir(chapter_path)
        log("Created dir: " + chapter_path)
        pages = request_chapter_data(chapter[1])
        log(f" Chapter {chapter[0]} pages: ", pages)
        name_format = '{:0' + str(len(str(len(pages)))) + 'd}' # 0-9 / 00-99 / 000-999 / ...
        for i, page in enumerate(pages):
            log("Requesting: " + page)
            headers = { 'Referer': "https://hachiraw.com/" }
            page_img_content = requests.get(page, headers=headers).content
            page_path = chapter_path + "/" + name_format.format(i) + ".jpg"
            open(page_path, 'wb').write(page_img_content)
            time.sleep(3) # otherwise it's pure DDoS, big nono


def request_manga_data(url) -> Manga:
    page = requests.get(url)
    soup = bs4(page.content, "html.parser") # same parser as default python

    manga_title = remove_raw_free(soup.title)
    manga_author = soup.select("div.authors-content > a")[0].string
    manga_artist = soup.select("div.artists-content > a")
    manga_artist = manga_artist[0].string if manga_artist else ""
    manga_description = soup.select("div.dsct > p")[0].string or "あらすじがない" # no desc
    manga_genres = soup.select("div.genres-content > a")
    manga_genres = list(map(lambda genre: genre.string, manga_genres))

    manga_chapters = soup.select("ul.list.row-content-chapter a.chapter-name")
    manga_chapters = list(map(lambda chapter: (chapter.contents[0], chapter['href']), manga_chapters))
    manga_chapters.reverse()

    log("title: ", manga_title)
    log("author: ", manga_author)
    log("artist: ", manga_artist)
    log("description: ", manga_description)
    log("genre: ", manga_genres)
    log("chapters: ", manga_chapters)

    return {
        "title": manga_title,
        "author": manga_author,
        "artist": manga_artist,
        "description": manga_description,
        "genre": manga_genres,
        "chapters": manga_chapters
        }


def run():
    manga_data = request_manga_data(URL)
    create_folder_structure_and_fill_chapters(manga_data)
