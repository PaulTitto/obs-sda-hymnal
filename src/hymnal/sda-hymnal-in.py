import requests
from bs4 import BeautifulSoup
import json
import time
import os
from dotenv import load_dotenv

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    )
}


def fetch_data(url):
    session = requests.Session()
    try:
        response = session.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error requesting {url}: {e}")
        return None


def extract_lagu(lagu, url):
    lagu_title = lagu.find("div", class_="judul")
    title_asli = lagu_title.get_text().split(" ")[2:] if lagu_title else []
    title = " ".join(title_asli).title() if title_asli else "Tanpa Judul"

    lirik_no_str = url.split("/")[-1]

    index_no = lirik_no_str.zfill(3)

    lirik = lagu.find("div", class_="lirik")
    daftar_bait = []
    daftar_reff = []

    if lirik:
        bait_reff = lirik.find("div", class_="bait reff")
        # if bait_reff:
        #     reff_lines = [line.get_text(strip=True) for line in bait_reff.find_all("div", class_="baris")]
        #     daftar_reff.append({
        #         "type": "refrain",
        #         "index": 0,
        #         "lines": reff_lines
        #     })

        bait_elements = lirik.find_all("div", class_="bait")
        for el in bait_elements:
            if "reff" in el.get("class", []):
                continue

            bait_no_div = el.find("div", class_="bait-no")
            bait_no = bait_no_div.get_text(strip=True) if bait_no_div else "0"

            bait_text_div = el.find("div", class_="bait-text")
            if bait_text_div:
                lines = [line.get_text(strip=True) for line in bait_text_div.find_all("div", class_="baris")]
                daftar_bait.append({
                    "type": "verse",
                    "index": int(bait_no) if bait_no.isdigit() else 0,
                    "lines": lines
                })

            if bait_reff:
                reff_lines = [line.get_text(strip=True) for line in bait_reff.find_all("div", class_="baris")]
                daftar_bait.append({
                    "type": "refrain",
                    "index": 0,
                    "lines": reff_lines
                })


    return {
        "index": index_no,
        "number": int(lirik_no_str),
        "title": title,
        "lyrics": daftar_bait
    }


def scrape_book(url):
    data = []
    content = fetch_data(url)
    if content:
        soup = BeautifulSoup(content, "html.parser")
        lagu_elements = soup.find_all("div", class_="lagu")
        for lagu in lagu_elements:
            hasil_ekstraksi = extract_lagu(lagu, url)
            data.append(hasil_ekstraksi)
    return data


load_dotenv()
base_url_raw = os.getenv("LAGU_SION_BASE_URL")

def main():
    output_file = "sda-hymnal-db-in.json"
    all_songs = []
    for i in range(1, 530):
        base_url = f"{base_url_raw}{i}"
        print(f"Scraping index {i}...")

        book_data = scrape_book(base_url)

        if book_data:
            all_songs.extend(book_data)
        else:
            all_songs.extend({
                "index": str(i).zfill(3),
                "number": i,
                "message": f"Data Kosong di {i} "
            })
            print(f"Data di indeks {i} kosong.")
            # break

        time.sleep(0.5)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_songs, f, indent=4, ensure_ascii=False)

    print(f"\nScraping complete! Total {len(all_songs)} songs saved to {output_file}")


if __name__ == '__main__':
    main()