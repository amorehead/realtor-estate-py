from webdriver_manager.firefox import GeckoDriverManager
from seleniumrequests import Firefox

driver = Firefox(executable_path=GeckoDriverManager().install())
request = driver.request('GET', "http://www.google.com/")
print(driver.title)
print(request)
driver.quit()
