from playwright.sync_api import Page, BrowserContext

from upwork_auto_login.exceptions import NotFoundElement


class UpworkActionsLogin:
    USERNAME_INPUT_LOCATOR = '#login_username'
    PASSWORD_INPUT_LOCATOR = '#login_password'

    def __init__(self, page: Page, username: str, password: str):
        self.page = page

        self.username = username
        self._password = password

    def fill_username(self) -> None:
        username_input = self.page.locator(self.USERNAME_INPUT_LOCATOR)

        if not username_input.is_visible():
            raise NotFoundElement('username input not visible!')

        username_input.fill(self.username)

    def wait_username_input(self) -> None:
        username_input = self.page.locator(self.USERNAME_INPUT_LOCATOR)
        username_input.wait_for(state='attached')

    def fill_password(self) -> None:
        password_input = self.page.locator(self.PASSWORD_INPUT_LOCATOR)

        if not password_input.is_visible():
            raise NotFoundElement('password input not visible!')

        password_input.fill(self._password)

    def wait_password_input(self) -> None:
        password_input = self.page.locator(self.PASSWORD_INPUT_LOCATOR)
        password_input.wait_for(state='attached')

    def click_continue(self) -> None:
        continue_button = self.page.locator('#login_password_continue')

        if not continue_button.is_visible():
            raise NotFoundElement('continue button not visible!')

        continue_button.click()

    def click_submit(self) -> None:
        submit_button = self.page.locator('#login_control_continue')

        if not submit_button.is_visible():
            raise NotFoundElement('submit button is not visible!')

        submit_button.click()

    def click_google_auth_button(self, context: BrowserContext) -> Page:
        google_button = self.page.locator('#login_google_submit')

        if not google_button.is_visible():
            raise NotFoundElement('google button is not visible!')

        with context.expect_page() as google_auth_page:
            google_button.click()

        return google_auth_page.value


class UpworkActionsGoogleAuth:
    EMAIL_INPUT_LOCATOR = 'xpath=//input[@type="email"]'
    PASSWORD_INPUT_LOCATOR = 'xpath=//input[@type="password"]'

    def __init__(self, page: Page, email: str, password: str):
        self.page = page
        self.email = email
        self._pwd = password

    def fill_google_email(self) -> None:
        email_input = self.page.locator(self.EMAIL_INPUT_LOCATOR)

        if not email_input.is_visible():
            raise ValueError('email input in google page not visible!')

        email_input.fill(self.email)

    def wait_email_input(self) -> None:
        email_input = self.page.locator(self.EMAIL_INPUT_LOCATOR)
        email_input.wait_for(state='attached')

    def fill_google_password(self) -> None:
        pwd_input = self.page.locator(self.PASSWORD_INPUT_LOCATOR)

        if not pwd_input.is_visible():
            raise NotFoundElement('password input in google page not visible!')

        pwd_input.fill(self._pwd)

    def wait_password_input(self) -> None:
        pwd_input = self.page.locator(self.PASSWORD_INPUT_LOCATOR)
        pwd_input.wait_for(state='attached')

    def click_google_continue_button(self, button_text: str = 'Next') -> None:
        button = self.page.locator(f'xpath=//span[contains(text(), "{button_text}")]/parent::button')

        if not button.is_visible():
            raise NotFoundElement('continue button with text %s not visible' % button_text)

        button.click()
