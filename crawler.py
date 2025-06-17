import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlencode
import os
import re

def sanitize_filename(filename):
    """
    Làm sạch một chuỗi để nó có thể được sử dụng làm tên file hợp lệ.
    """
    # Xóa các ký tự không hợp lệ cho tên file
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    # Thay thế khoảng trắng bằng gạch dưới
    sanitized = sanitized.replace(' ', '_')
    # Giới hạn độ dài tên file để tránh lỗi hệ thống
    return sanitized[:150]

def get_and_save_article(article_url, directory):
    """
    Truy cập URL của một bài viết, trích xuất nội dung và lưu thành file .txt.

    Args:
        article_url (str): URL của bài viết.
        directory (str): Thư mục để lưu file txt.
    """
    try:
        print(f"  -> Đang xử lý: {article_url}")
        response = requests.get(article_url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # --- Trích xuất tiêu đề và nội dung ---
        # Selector cho tiêu đề thường là thẻ <h1> trong trang chi tiết
        title_element = soup.select_one('h1.title-page.detail')
        if not title_element: # Thử selector dự phòng
            title_element = soup.select_one('h1')

        # Selector cho nội dung chính của bài viết
        content_element = soup.select_one('div.article-content')

        if not title_element or not content_element:
            print(f"  [Lỗi] Không tìm thấy tiêu đề hoặc nội dung cho: {article_url}")
            return

        title = title_element.get_text(strip=True)
        # Lấy văn bản, dùng separator='\n' để giữ lại các dòng xuống dòng (đoạn văn)
        content = content_element.get_text(separator='\n', strip=True)

        # --- Lưu file ---
        filename = sanitize_filename(title) + ".txt"
        filepath = os.path.join(directory, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"TIÊU ĐỀ: {title}\n\n")
            f.write(f"URL: {article_url}\n\n")
            f.write("------------------ NỘI DUNG ------------------\n\n")
            f.write(content)
        
        print(f"  [Thành công] Đã lưu bài viết vào file: {filepath}")

    except requests.exceptions.RequestException as e:
        print(f"  [Lỗi] Không thể truy cập bài viết {article_url}: {e}")
    except Exception as e:
        print(f"  [Lỗi] Xảy ra lỗi không xác định khi xử lý {article_url}: {e}")


def crawl_sbv_news(base_url, output_dir='sbv_articles'):
    """
    Crawls a paginated list, extracts content from each link, and saves to files.

    Args:
        base_url (str): The starting URL of the article list.
        output_dir (str): The directory to save the article files.
    """
    # Tạo thư mục lưu trữ nếu chưa tồn tại
    os.makedirs(output_dir, exist_ok=True)
    
    crawled_urls = set() # Dùng set để kiểm tra các URL đã xử lý nhanh hơn
    
    parsed_url = urlparse(base_url)
    page_param_name = 'page_number_e606ff5c-6c97-c51f-695e-e5bcf26917ec'
    url_without_query = parsed_url._replace(query=None).geturl()

    page_number = 298 
    
    while True:
        params = {page_param_name: page_number}
        current_url = f"{url_without_query}?{urlencode(params)}"
        
        print(f"\nĐang crawl trang danh sách: {page_number} - URL: {current_url}")

        try:
            response = requests.get(current_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # **Selector này cần được điều chỉnh cho đúng với trang mục tiêu**
            article_links = soup.select('.other-news-articles h5 a')

            if not article_links:
                print("Không tìm thấy bài viết nào trên trang này. Kết thúc crawl.")
                break

            found_new_article = False
            for link in article_links:
                article_url = urljoin(base_url, link['href'])
                
                if article_url not in crawled_urls:
                    found_new_article = True
                    crawled_urls.add(article_url)
                    # Lấy nội dung và lưu file
                    get_and_save_article(article_url, output_dir)

            if not found_new_article:
                print("Không có bài viết mới trên trang này. Dừng lại.")
                break
                
            page_number += 1

        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi truy cập trang danh sách: {e}")
            break
            
    print(f"\nHoàn tất! Tổng cộng đã xử lý {len(crawled_urls)} bài viết.")
    print(f"Tất cả các file đã được lưu trong thư mục: '{os.path.abspath(output_dir)}'")


if __name__ == '__main__':
    # URL từ yêu cầu của bạn, trỏ tới một danh sách bài viết có phân trang
    # Ta sẽ dùng một URL chuyên mục ví dụ từ sbv.gov.vn
    start_url = "https://sbv.gov.vn/vi/w/th%E1%BB%91ng-%C4%91%E1%BB%91c-nguy%E1%BB%85n-th%E1%BB%8B-h%E1%BB%93ng-tham-gia-gi%E1%BA%A3i-%C4%91i-b%E1%BB%99-ch%E1%BA%A1y-b%E1%BB%99-t%E1%BB%B1-h%C3%A0o-th%C3%A0nh-ph%E1%BB%91-t%C3%B4i-y%C3%AAu-"
    
    # Bạn có thể thay thế start_url bằng URL bạn muốn crawl, ví dụ:
    # start_url = "https://sbv.gov.vn/vi/web/guest/tin-tuc-su-kien/tin-chuyen-nganh"

    crawl_sbv_news(start_url)
