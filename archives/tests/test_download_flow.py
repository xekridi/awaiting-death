from tempfile import NamedTemporaryFile
from zipfile import ZipFile

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

class DownloadFlowSeleniumTest(StaticLiveServerTestCase):
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

    '''def test_download_with_limit_and_password(self):
        driver = self.driver
        wait = WebDriverWait(driver, 10)

        driver.get(self.live_server_url + "/signup/")
        driver.find_element(By.NAME, "username").send_keys("u1")
        driver.find_element(By.NAME, "email").send_keys("u1@example.com")
        driver.find_element(By.NAME, "password1").send_keys("pass12345")
        driver.find_element(By.NAME, "password2").send_keys("pass12345")
        driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        wait.until(EC.url_to_be(self.live_server_url + "/"))

        driver.find_element(By.LINK_TEXT, "Загрузить").click()
        tmp = NamedTemporaryFile(suffix=".txt", delete=False)
        tmp.write(b"hello")
        tmp.flush()
        driver.find_element(By.NAME, "files").send_keys(tmp.name)
        driver.find_element(By.NAME, "description").send_keys("desc")
        driver.find_element(By.NAME, "password1").send_keys("sec")
        driver.find_element(By.NAME, "password2").send_keys("sec")
        driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "h4"), "Ваш архив собирается"))

        driver.execute_script("""
            fetch("/api/archives/" + window.location.pathname.split("/")[2] + "/stats/", {
                method: "PATCH",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({ready:true, max_downloads:1, password:"sec"})
            });
        """)

        wait.until(EC.url_contains("/d/"))
        driver.get(driver.current_url.split("?")[0])
        assert "403" in driver.page_source
        driver.get(driver.current_url + "?password=sec")
        assert "Forbidden" not in driver.page_source'''
