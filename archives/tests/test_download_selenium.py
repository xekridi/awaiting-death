import os
import zipfile
import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from archives.models import Archive

@pytest.mark.selenium
class DownloadFlowSeleniumTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        try:
            cls.driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=options
            )
        except Exception:
            pytest.skip("ChromeDriver не доступен — пропускаем selenium-тесты", allow_module_level=True)
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        self.wait_arch = Archive.objects.create(
            name="name", 
            short_code="sel-wait",
            ready=False,
            max_downloads=0
        )

        self.ready_arch = Archive.objects.create(
            name="name", 
            short_code="sel-ready",
            ready=True,
            max_downloads=0,
        )
        zip_name = f"{self.ready_arch.short_code}.zip"
        path = os.path.join(settings.MEDIA_ROOT, zip_name)
        with zipfile.ZipFile(path, "w") as zf:
            zf.writestr("foo.txt", "foo")
            zf.writestr("bar.txt", "bar")
        self.ready_arch.zip_file.name = zip_name
        self.ready_arch.save(update_fields=["zip_file"])

    def test_preview_wait(self):
        url = f"{self.live_server_url}/d/{self.wait_arch.short_code}/preview/"
        self.driver.get(url)
        body = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Пожалуйста, подождите", body)

    def test_preview_ready_shows_file_list_and_download_link(self):
        url = f"{self.live_server_url}/d/{self.ready_arch.short_code}/preview/"
        self.driver.get(url)
        items = self.driver.find_elements(By.TAG_NAME, "li")
        texts = [li.text for li in items]
        self.assertIn("foo.txt", texts)
        self.assertIn("bar.txt", texts)
        link = self.driver.find_element(By.CSS_SELECTOR, "a.btn")
        href = link.get_attribute("href")
        expected = f"/d/{self.ready_arch.short_code}/file/"
        self.assertTrue(href.endswith(expected))