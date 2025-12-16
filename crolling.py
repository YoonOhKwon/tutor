from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json

def crawl_all_notices(user_id, user_pw):

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    driver.get("https://wis.hufs.ac.kr/src08/jsp/twofactor_login.jsp")

    wait.until(EC.presence_of_element_located((By.NAME, "user_id")))
    driver.find_element(By.NAME, "user_id").send_keys(user_id)
    driver.find_element(By.ID, "password").send_keys(user_pw)
    driver.find_element(By.ID, "login_btn").click()

    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "em.sub_open")))
    courses = driver.find_elements(By.CSS_SELECTOR, "em.sub_open")
    
    course_titles = [
        c.get_attribute("title")
         .replace("강의실 들어가기", "")
         .replace("  ", " ")
         .strip()
        for c in courses
    ]

    notice_titles = []
    notice_contents = []

    for i in range(len(course_titles)):
        driver.get("https://eclass.hufs.ac.kr/ilos/main/main_form.acl")
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "em.sub_open")))

        courses = driver.find_elements(By.CSS_SELECTOR, "em.sub_open")
        driver.execute_script("arguments[0].click();", courses[i])

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img[alt='공지사항']")))
        driver.find_element(By.CSS_SELECTOR, "img[alt='공지사항']").click()

        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr.list, tr[style*='cursor: pointer']")))
        notices = driver.find_elements(By.CSS_SELECTOR, "tr.list, tr[style*='cursor: pointer']")

        lecture_titles = []
        lecture_contents = []

        for j in range(len(notices)):
            notices = driver.find_elements(By.CSS_SELECTOR, "tr.list, tr[style*='cursor: pointer']")

            try:
                title = notices[j].find_element(By.CSS_SELECTOR, "div.subjt_top").text.strip()
            except:
                title = "(제목 없음)"

            lecture_titles.append(title)

            driver.execute_script("arguments[0].click();", notices[j].find_element(By.CSS_SELECTOR, "a.site-link"))
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "td.textviewer")))

            try:
                content = driver.find_element(By.CSS_SELECTOR, "td.textviewer").text.strip()
            except:
                content = "(내용 없음)"

            lecture_contents.append(content)
            driver.back()

        notice_titles.append(lecture_titles)
        notice_contents.append(lecture_contents)

    driver.quit()

    with open("cache_titles.json", "w", encoding="utf-8") as f:
        json.dump(notice_titles, f, ensure_ascii=False, indent=2)

    with open("cache_contents.json", "w", encoding="utf-8") as f:
        json.dump(notice_contents, f, ensure_ascii=False, indent=2)

    return notice_titles, notice_contents, course_titles


