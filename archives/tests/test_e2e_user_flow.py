'''from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

class UserE2ETest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def test_signup_and_login(self):
        driver = self.driver
        wait = WebDriverWait(driver, 10)
        driver.get(self.live_server_url + reverse("signup"))
        driver.find_element(By.NAME, "username").send_keys("user1")
        driver.find_element(By.NAME, "email").send_keys("user1@example.com")
        driver.find_element(By.NAME, "password1").send_keys("password123")
        driver.find_element(By.NAME, "password2").send_keys("password123")
        driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        wait.until(EC.url_to_be(self.live_server_url + "/"))
        driver.get(self.live_server_url + reverse("logout"))
        driver.get(self.live_server_url + reverse("login"))
        driver.find_element(By.NAME, "username").send_keys("user1")
        driver.find_element(By.NAME, "password").send_keys("password123")
        driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        wait.until(EC.url_to_be(self.live_server_url + "/"))

    def test_upload_wait_and_download(self):
        driver = self.driver
        wait = WebDriverWait(driver, 10)
        driver.get(self.live_server_url + reverse("signup"))
        driver.find_element(By.NAME, "username").send_keys("user2")
        driver.find_element(By.NAME, "email").send_keys("user2@example.com")
        driver.find_element(By.NAME, "password1").send_keys("password123")
        driver.find_element(By.NAME, "password2").send_keys("password123")
        driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        wait.until(EC.url_to_be(self.live_server_url + "/"))
        driver.find_element(By.LINK_TEXT, "Загрузить").click()
        tmp = NamedTemporaryFile(suffix=".txt", delete=False)
        tmp.write(b"hello world")
        tmp.flush()
        driver.find_element(By.NAME, "files").send_keys(tmp.name)
        driver.find_element(By.NAME, "description").send_keys("e2e test")
        driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "h4"), "Ваш архив собирается"))
        code = driver.current_url.split("/")[-2]
        driver.execute_script(
            "fetch('/api/archives/%s/status/',{method:'PATCH',headers:{'Content-Type':'application/json'},"
            "body:JSON.stringify({ready:true})});" % code
        )
        wait.until(EC.url_contains("/d/"))
        driver.get(driver.current_url)
        assert "attachment" in driver.page_source or driver.response_headers.get("Content-Disposition")

    def test_dashboard_and_stats(self):
        driver = self.driver
        wait = WebDriverWait(driver, 10)
        driver.get(self.live_server_url + reverse("signup"))
        driver.find_element(By.NAME, "username").send_keys("user3")
        driver.find_element(By.NAME, "email").send_keys("user3@example.com")
        driver.find_element(By.NAME, "password1").send_keys("password123")
        driver.find_element(By.NAME, "password2").send_keys("password123")
        driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        wait.until(EC.url_to_be(self.live_server_url + "/"))
        driver.find_element(By.LINK_TEXT, "Загрузить").click()
        tmp = NamedTemporaryFile(suffix=".txt", delete=False)
        tmp.write(b"data")
        tmp.flush()
        driver.find_element(By.NAME, "files").send_keys(tmp.name)
        driver.find_element(By.NAME, "description").send_keys("stats test")
        driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "h4"), "Ваш архив собирается"))
        code = driver.current_url.split("/")[-2]
        driver.get(self.live_server_url + reverse("dashboard"))
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, code)))
        driver.find_element(By.LINK_TEXT, code).click()
        wait.until(EC.url_contains("/dashboard/"))
        driver.find_element(By.LINK_TEXT, "Статистика").click()
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "canvas")))'''