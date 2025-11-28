import re
import csv
import time
from playwright.sync_api import sync_playwright


# 제목에서 용량 추출
def extract_capacity_from_title(title: str):
    """
    제목 내부의 용량 패턴을 탐지: 300g, 70매, 800ml, 1개, 70매 x 10개 등
    """
    patterns = [
        r"(\d+)\s?(g|ml)",
        r"(\d+)\s?(매|개|입|팩)",
        r"(\d+)\s?x\s?(\d+)\s?(매|개|입|팩)"
    ]

    for p in patterns:
        m = re.search(p, title.lower())
        if m:
            return m.groups()

    return None

# 단위가격 파싱
def extract_unit_price(text: str):
    text = text.replace(",", "")
    pattern = r"(\d+)\s?원/\s?(\d+)(g|ml|매|개)"
    m = re.search(pattern, text)
    if m:
        price, unit_val, unit_type = m.groups()
        return {
            "unit_price": int(price),
            "unit_value": int(unit_val),
            "unit_type": unit_type
        }
    return None

# 상세 페이지 크롤러
def crawl_info_page(page, url):
    time.sleep(0.8)  # 차단 방지 딜레이

    page.goto(url)
    page.wait_for_load_state("domcontentloaded")

    title = page.locator("span.title").inner_text().strip()
    capacity = extract_capacity_from_title(title)

    option_items = page.locator("ul.list__variant-selector > li")
    count = option_items.count()

    results = []

    for i in range(count):
        item = option_items.nth(i)

        # 가격
        price_raw = item.locator(".text__num").inner_text().replace(",", "")
        price = int(price_raw)

        # 단위가격
        unit_price_raw = item.locator(".text__unit-price").inner_text().strip()
        unit_info = extract_unit_price(unit_price_raw) if unit_price_raw else None

        # 옵션명
        spec = item.locator(".text__spec").inner_text().strip()

        # pcode 추출
        link = item.locator("a.link__full").get_attribute("href")
        m = re.search(r"pcode=(\d+)", link)
        pcode = m.group(1) if m else None

        results.append({
            "product_title": title,
            "capacity": capacity,
            "option_spec": spec,
            "price": price,
            "unit_price": unit_info,
            "pcode": pcode,
            "detail_url": url
        })

    return results

# 페이지네이션 이동 (~10p)
def goto_page(page, page_number: int):
    btn = page.locator(f"a.num:has-text('{page_number}')").first

    if btn.count() == 0:
        return False

    time.sleep(0.8)  # 페이지 이동 전 딜레이

    try:
        btn.click()
    except:
        return False

    try:
        page.wait_for_load_state("domcontentloaded", timeout=3000)
    except:
        pass

    # 리스트가 다시 뜰 때까지 대기
    try:
        page.locator("li.prod_item").first.wait_for(timeout=5000)
    except:
        pass

    return True

# 카테고리 전체 페이지 → 상품 URL 수집
def crawl_category_all_pages(page, category_url, max_pages=50):
    print(f"[카테고리 시작] {category_url}")

    page.goto(category_url)
    page.wait_for_load_state("domcontentloaded")
    time.sleep(0.8)

    product_urls = []

    for p in range(1, max_pages + 1):
        print(f"[카테고리] {p} 페이지 크롤링 중...")

        items = page.locator("li.prod_item .prod_main_info a.thumb_link")
        count = items.count()

        if count == 0:
            print("[카테고리] 상품을 찾을 수 없음 → 종료")
            break

        print(f" → 상품 {count}개 수집")

        for i in range(count):
            url = items.nth(i).get_attribute("href")
            if url and url.startswith("http"):
                product_urls.append(url)

        # 페이지 이동
        moved = goto_page(page, p + 1)
        if not moved:
            print("[카테고리] 다음 페이지 없음 → 종료")
            break

    return product_urls


# 전체 파이프라인
def crawl_category(category_url, output_csv="result.csv"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # 링크 수집
        urls = crawl_category_all_pages(page, category_url)
        print(f"[총 수집된 상품 URL] {len(urls)}개")

        results = []

        # 상세 크롤링
        for idx, url in enumerate(urls, start=1):
            print(f"[상세] {idx}/{len(urls)} → {url}")

            try:
                info = crawl_info_page(page, url)
                results.extend(info)
            except Exception as e:
                print(f"[오류 발생] {url} → {e}")

        browser.close()

    # CSV 저장
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "product_title", "capacity", "option_spec",
            "price", "unit_price", "pcode", "detail_url"
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"[완료] CSV 저장 → {output_csv}")


# 7) 실제 실행
if __name__ == "__main__":
    crawl_category(
        "https://prod.danawa.com/list/?cate=16249098", # 크롤링 대상 카테고리 링크
        "danawa_unit_result.csv" # 파일 이름
    )
