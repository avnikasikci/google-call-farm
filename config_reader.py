import json
import multiprocessing
from dataclasses import dataclass
from typing import Optional

from logger import logger


@dataclass
class PathParams:
    query_file: str
    page_in_query_file: str
    proxy_file: str
    user_agents: Optional[str] = "user_agents.txt"
    filtered_domains: Optional[str] = "domains.txt"


@dataclass
class WebdriverParams:
    proxy: str
    auth: Optional[bool] = False
    incognito: Optional[bool] = False
    country_domain: Optional[bool] = False
    language_from_proxy: Optional[bool] = False
    ss_on_exception: Optional[bool] = False
    window_size: Optional[str] = ""
    shift_windows: Optional[bool] = False


@dataclass
class BehaviorParams:
    query: str
    min_non_ads_click: Optional[int] = 2
    max_non_ads_click: Optional[int] = 3
    page_min_wait: Optional[int] = 10
    page_max_wait: Optional[int] = 15
    max_scroll_limit: Optional[int] = 0
    check_only_adsclick_domain: Optional[bool] = True
    excludes: Optional[str] = ""
    random_mouse: Optional[bool] = False
    custom_cookies: Optional[bool] = False
    click_order: Optional[int] = 5
    browser_count: Optional[int] = 2
    multiprocess_style: Optional[int] = 1
    loop_wait_time: Optional[int] = 60
    running_interval_start: Optional[str] = ""
    running_interval_end: Optional[str] = ""
    twocaptcha_apikey: Optional[str] = ""
    hooks_enabled: Optional[bool] = False
    telegram_enabled: Optional[bool] = False
    send_to_android: Optional[bool] = False


class ConfigReader:
    """Config file reader"""

    def __init__(self) -> None:
        self.paths = None
        self.webdriver = None
        self.behavior = None

    def read_parameters(self) -> None:
        """Read parameters from the config.json file"""

        with open("config.json", encoding="utf-8") as config_file:
            try:
                config = json.loads(config_file.read())
            except Exception:
                logger.error("Failed to read config file. Check format and try again.")
                raise SystemExit()

        self.paths = PathParams(
            query_file=config["paths"]["query_file"],
            page_in_query_file=config["paths"]["page_in_query_file"],
            proxy_file=config["paths"]["proxy_file"],
            user_agents=config["paths"]["user_agents"],
            filtered_domains=config["paths"]["filtered_domains"],
        )

        if self.paths.proxy_file and config["webdriver"]["proxy"]:
            logger.error("Either 'proxy_file' or 'proxy' parameter should be empty.")
            raise SystemExit()

        self.webdriver = WebdriverParams(
            proxy=config["webdriver"]["proxy"],
            auth=config["webdriver"]["auth"],
            incognito=config["webdriver"]["incognito"],
            country_domain=config["webdriver"]["country_domain"],
            language_from_proxy=config["webdriver"]["language_from_proxy"],
            ss_on_exception=config["webdriver"]["ss_on_exception"],
            window_size=config["webdriver"]["window_size"],
            shift_windows=config["webdriver"]["shift_windows"],
        )

        #if self.paths.query_file and config["behavior"]["query"]:
            #logger.error("Either 'query_file' or 'query' parameter should be empty.")
            #raise SystemExit()

        browser_count = config["behavior"]["browser_count"]

        self.behavior = BehaviorParams(
            query=config["behavior"]["query"],
            min_non_ads_click=config["behavior"]["min_non_ads_click"],
            max_non_ads_click=config["behavior"]["max_non_ads_click"],
            page_min_wait=config["behavior"]["page_min_wait"],
            page_max_wait=config["behavior"]["page_max_wait"],
            max_scroll_limit=config["behavior"]["max_scroll_limit"],
            check_only_adsclick_domain=config["behavior"]["check_only_adsclick_domain"],
            excludes=config["behavior"]["excludes"],
            random_mouse=config["behavior"]["random_mouse"],
            custom_cookies=config["behavior"]["custom_cookies"],
            click_order=config["behavior"]["click_order"],
            browser_count=multiprocessing.cpu_count() if browser_count == 0 else browser_count,
            multiprocess_style=config["behavior"]["multiprocess_style"],
            loop_wait_time=config["behavior"]["loop_wait_time"],
            running_interval_start=config["behavior"]["running_interval_start"],
            running_interval_end=config["behavior"]["running_interval_end"],
            twocaptcha_apikey=config["behavior"]["2captcha_apikey"],
            hooks_enabled=config["behavior"]["hooks_enabled"],
            telegram_enabled=config["behavior"]["telegram_enabled"],
            send_to_android=config["behavior"]["send_to_android"],
        )


config = ConfigReader()
config.read_parameters()
