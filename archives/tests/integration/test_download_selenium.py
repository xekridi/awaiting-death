import os
import zipfile

import pytest
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from archives.models.archive import Archive


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
            pytest.skip("ChromeDriver not available", allow_module_level=True)
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        self.wait_arch = Archive.objects.create(short_code="sel-wait", ready=False, name="selenium")
        self.ready_arch = Archive.objects.create(short_code="sel-ready", ready=True, name="selenium")
        zip_name = f"{self.ready_arch.short_code}.zip"
        zip_path = os.path.join(settings.MEDIA_ROOT, zip_name)
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("foo.txt", "foo")
            zf.writestr("bar.txt", "bar")
        self.ready_arch.zip_file.name = zip_name
        self.ready_arch.save(update_fields=["zip_file"])

    def test_preview_wait(self):
        url = f"{self.live_server_url}/d/{self.wait_arch.short_code}/preview/"
        self.driver.get(url)
        body = self.driver.find_element(By.TAG_NAME, "body").text
        assert "Пожалуйста, подождите" in body

    def test_preview_ready_shows_files_and_download_link(self):
        url = f"{self.live_server_url}/d/{self.ready_arch.short_code}/preview/"
        self.driver.get(url)
        items = self.driver.find_elements(By.TAG_NAME, "li")
        filenames = [item.text for item in items]
        assert "foo.txt" in filenames
        assert "bar.txt" in filenames
        link = self.driver.find_element(By.CSS_SELECTOR, "a.btn")
        href = link.get_attribute("href")
        assert href.endswith(f"/d/{self.ready_arch.short_code}/file/")
