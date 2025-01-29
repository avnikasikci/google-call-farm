import random
import shutil
import string
import traceback
from argparse import ArgumentParser
from datetime import datetime
from itertools import chain, filterfalse, zip_longest
from pathlib import Path

import hooks
from clicklogs_db import ClickLogsDB
from config_reader import config
from logger import logger, update_log_formats
from live_logger import live_logger, live_update_log_formats
from proxy import get_proxies
from search_controller import SearchController
from utils import (
    get_random_user_agent_string,
    get_domains,
    take_screenshot,
    generate_click_report,
    get_queries,
    get_ads_queries
)
from webdriver import create_webdriver


if config.behavior.telegram_enabled:
    from telegram_notifier import notify_matching_ads, start_bot


__author__ = "Coşkun Deniz <coskun.denize@gmail.com>"


def get_arg_parser() -> ArgumentParser:
    """Get argument parser

    :rtype: ArgumentParser
    :returns: ArgumentParser object
    """

    arg_parser = ArgumentParser(add_help=False, usage="See README.md file")
    arg_parser.add_argument("-q", "--query", help="Search query")
    arg_parser.add_argument("-qa", "--query-ads", dest="ads_query", help="Search ads query")
    arg_parser.add_argument(
        "-p",
        "--proxy",
        help="""Use the given proxy in "ip:port" or "username:password@host:port" format""",
    )
    arg_parser.add_argument("--id", help="Browser id for multiprocess run")
    arg_parser.add_argument(
        "--enable_telegram", action="store_true", help="Enable telegram notifications"
    )
    arg_parser.add_argument(
        "--report_clicks", action="store_true", help="Get click report for the given date"
    )
    arg_parser.add_argument("--date", help="Give a specific report date in DD-MM-YYYY format")
    arg_parser.add_argument("--excel", action="store_true", help="Write results to an Excel file")
    arg_parser.add_argument(
        "--check_nowsecure", action="store_true", help="Check nowsecure.nl for undetection"
    )
    arg_parser.add_argument("-d", "--device_id", help="Android device ID for assigning to browser")

    return arg_parser

def main_click_one_step(args,queries,ads_query):
    """Entry point for the tool"""
    print("im am main click for now ")
    print(queries)
    if args.report_clicks:
        report_date = datetime.now().strftime("%d-%m-%Y") if not args.date else args.date

        clicklogs_db_client = ClickLogsDB()
        click_results = clicklogs_db_client.query_clicks(click_date=report_date)

        border = (
            "+" + "-" * 70 + "+" + "-" * 27 + "+" + "-" * 9 + "+" + "-" * 12 + "+" + "-" * 12 + "+"
        )

        if click_results:
            print(border)
            print(
                f"| {'URL':68s} | {'Query':25s} | {'Clicks':7s} | {'Time':10s} | {'Category':10s} |"
            )
            print(border)

            for result in click_results:
                url, clicks, category, click_time, search_query = result

                if len(url) > 68:
                    url = url[:65] + "..."

                print(
                    f"| {url:68s} | {search_query:25s} | {str(clicks):7s} | {click_time:10s} | {category:10s} |"
                )

                print(border)

            # write results to Excel with name click_report_dd-mm-yyyy.xlsx
            if args.excel:
                generate_click_report(click_results, report_date)

        else:
            logger.info(f"No click result was found for {report_date}!")

        return

    if args.enable_telegram:
        if config.behavior.telegram_enabled:
            start_bot()
            return
        else:
            logger.info("Please set the telegram_enabled option to true in config and try again.")
            return

    if args.id:
        update_log_formats(args.id)
    #else:
        #if not config.behavior.query:
            #logger.error("Fill the query parameter!")
            #raise SystemExit()

        #query = config.behavior.query

    if args.proxy:
        proxy = args.proxy
    elif config.paths.proxy_file:
        proxies = get_proxies()
        logger.debug(f"Proxies: {proxies}")
        proxy = random.choice(proxies)
    elif config.webdriver.proxy:
        proxy = config.webdriver.proxy
    else:
        proxy = None

    domains = get_domains()
    user_agent = get_random_user_agent_string()
    plugin_folder_name = "".join(random.choices(string.ascii_lowercase, k=5))
    driver, country_code = create_webdriver(proxy, user_agent, plugin_folder_name)
  
    if args.check_nowsecure:
        from time import sleep

        driver.get("https://nowsecure.nl/")
        sleep(7)

        driver.quit()

        raise SystemExit()

    if config.behavior.hooks_enabled:
        hooks.before_search_hook(driver)

    search_controller = None
    try:
        search_index = 0
        search_controller = SearchController(driver, "", country_code)
        for query_for in queries: #reklamsız tıklama ve reklamlı tıklama query farklı olacak burada
            if isinstance(query_for, str):  # Sadece string olan öğeleri işleme al
                print(query_for.upper())
                search_index = search_index + 1
                live_logger.info(f"{search_index}. arama işlemi yapılıyor.")
                try:
                        if args.id:
                            search_controller.set_browser_id(args.id)

                        if args.device_id:
                            search_controller.assign_android_device(args.device_id)
                        ads, non_ad_links, shopping_ads = search_controller.search_for_ads(query_for,non_ad_domains=domains)
                        ads = []
                        #yukarıdaki reklamsız linkleri buldu bunlara şimdi tıklatıcaz.
                        search_controller.click_links(None,domains,False)
                        print(f"hata kodlari special =0> {non_ad_links}")
                        if config.behavior.hooks_enabled:
                            hooks.after_search_hook(driver)

                        if not (ads or shopping_ads or non_ad_links):
                            logger.info("Classic No ads found in the search results!")

                            if config.behavior.telegram_enabled:
                                notify_matching_ads(query_for, links=None, stats=search_controller.stats)
                        else:
                            logger.debug(f"Selected click order: {config.behavior.click_order}")

                            if config.behavior.click_order == 1:
                                all_links = non_ad_links + ads

                            elif config.behavior.click_order == 2:
                                all_links = ads + non_ad_links

                            elif config.behavior.click_order == 3:
                                if non_ad_links:
                                    all_links = [non_ad_links[0]] + [ads[0]] + non_ad_links[1:] + ads[1:]
                                else:
                                    logger.debug("Couldn't found non-ads! Continue with ads only.")
                                    all_links = ads

                            elif config.behavior.click_order == 4:
                                all_links = list(
                                    filterfalse(
                                        lambda x: not x, chain.from_iterable(zip_longest(non_ad_links, ads))
                                    )
                                )

                            else:
                                all_links = ads + non_ad_links
                                random.shuffle(all_links)

                            logger.info(f"Found {len(ads) + len(shopping_ads)} ads")
                            search_controller.click_shopping_ads(shopping_ads)
                            search_controller.click_links(all_links,domains,False)
                            
                            if config.behavior.hooks_enabled:
                                hooks.after_clicks_hook(driver)

                            if config.behavior.telegram_enabled:
                                notify_matching_ads(query_for, links=ads + shopping_ads, stats=search_controller.stats)

                            logger.info(search_controller.stats)

                except Exception as exp:
                    logger.error(f"Exception for occurred. See the details in the log file.{exp}")

                    if config.webdriver.ss_on_exception:
                        take_screenshot(driver)
                    message = str(exp).split("\n")[0]
                    logger.debug(f"Exception: {message}")
                    details = traceback.format_tb(exp.__traceback__)
                    logger.debug(f"Exception details: \n{''.join(details)}")            
      
        #reklamsız tık senaryosu başlatılsın.
        if(isinstance(ads_query,str)):
            logger.debug("*********İşlemler başlatıldı, bir kez random reklamlı tıklama yapılacak.1 sırada ki reklamlardan bir tanesine tıklama yapılacak.")
            live_logger.info(f"İşlemler başlatıldı, bir kez random reklamlı tıklama yapılacak. Random sıradaki reklamlardan bir tanesine tıklama yapılacak.")
            try:
                        if args.id:
                            search_controller.set_browser_id(args.id)

                        if args.device_id:
                            search_controller.assign_android_device(args.device_id)
                        ads, non_ad_links, shopping_ads = search_controller.search_for_ads(ads_query,non_ad_domains=domains)
                        non_ad_links = []
                        #yukarıdaki reklamsız linkleri buldu bunlara şimdi tıklatıcaz.
                        search_controller.click_links(None,domains,True)
                        print(f"hata kodlari special =0> {non_ad_links}")
                        if config.behavior.hooks_enabled:
                            hooks.after_search_hook(driver)

                        if not (ads or shopping_ads or non_ad_links):
                            logger.info("Classic No ads found in the search results!")

                            if config.behavior.telegram_enabled:
                                notify_matching_ads(ads_query, links=None, stats=search_controller.stats)
                        else:
                            logger.debug(f"Selected click order: {config.behavior.click_order}")

                            if config.behavior.click_order == 1:
                                all_links = non_ad_links + ads

                            elif config.behavior.click_order == 2:
                                all_links = ads + non_ad_links

                            elif config.behavior.click_order == 3:
                                if non_ad_links:
                                    all_links = [non_ad_links[0]] + [ads[0]] + non_ad_links[1:] + ads[1:]
                                else:
                                    logger.debug("Couldn't found non-ads! Continue with ads only.")
                                    all_links = ads

                            elif config.behavior.click_order == 4:
                                all_links = list(
                                    filterfalse(
                                        lambda x: not x, chain.from_iterable(zip_longest(non_ad_links, ads))
                                    )
                                )

                            else:
                                all_links = ads + non_ad_links
                                random.shuffle(all_links)

                            #logger.info(f"Found {len(ads) + len(shopping_ads)} ads")
                            search_controller.click_shopping_ads(shopping_ads)
                            search_controller.click_links(all_links,domains,True)
                            
                            if config.behavior.hooks_enabled:
                                hooks.after_clicks_hook(driver)

                            if config.behavior.telegram_enabled:
                                notify_matching_ads(ads_query, links=ads + shopping_ads, stats=search_controller.stats)

                            logger.info(search_controller.stats)

            except Exception as exp:
                    logger.error("Exception for occurred. See the details in the log file.")
                    if config.webdriver.ss_on_exception:
                        take_screenshot(driver)
                    message = str(exp).split("\n")[0]
                    logger.debug(f"Exception: {message}")
                    details = traceback.format_tb(exp.__traceback__)
                    logger.debug(f"Exception details: \n{''.join(details)}")    
    except Exception as exp:
        logger.error("Exception occurred. See the details in the log file.")

        if config.webdriver.ss_on_exception:
            take_screenshot(driver)

        message = str(exp).split("\n")[0]
        logger.debug(f"Exception: {message}")
        details = traceback.format_tb(exp.__traceback__)
        logger.debug(f"Exception details: \n{''.join(details)}")

        logger.debug(f"Exception cause: {exp.__cause__}") if exp.__cause__ else None

        if config.behavior.hooks_enabled:
            hooks.exception_hook(driver)

    finally:
        if search_controller:
            if config.behavior.hooks_enabled:
                hooks.before_browser_close_hook(driver)

            search_controller.end_search()

            if config.behavior.hooks_enabled:
                hooks.after_browser_close_hook(driver)

        if proxy and config.webdriver.auth:
            plugin_folder = Path.cwd() / "proxy_auth_plugin" / plugin_folder_name
            logger.debug(f"Removing '{plugin_folder}' folder...")
            shutil.rmtree(plugin_folder, ignore_errors=True)

def main():
        start_index = 0
        arg_parser = get_arg_parser()
        args = arg_parser.parse_args()

        if args.query:
            query = args.query

        if args.ads_query:
            ads_query = args.ads_query

        queries = []
        if config.paths.query_file:
            queries = get_queries()
        else:
            queries.append(query)

        ads_queries = []
        if config.paths.page_in_query_file:
            ads_queries = get_ads_queries()
        else:
            ads_queries.append(ads_query)

        while start_index < len(queries):
            # Rastgele tıklama sayısı belirleme
            min_click = config.behavior.min_non_ads_click
            max_click = config.behavior.max_non_ads_click  # max değerini doğru şekilde almayı unutmayın
            randClickCount = random.randint(min_click, max_click)
            live_logger.info(f"İşlemler başlatıldı, toplam {randClickCount} adet reklamsız tıklama araması yapılacak.")

            # Reklamsız tıklama işlemleri
            end_index = start_index + randClickCount
            queries_list= []
            for i in range(start_index, end_index):
                if i >= len(queries):
                    break
                query = queries[i]
                queries_list.append(queries[i])
                # Reklamsız tıklama işlemini gerçekleştir
                # Örneğin: non_ad_click_function(query)
            print("query list ")
            print(queries_list)
            ads_query_rand = random.choice(ads_queries)
            print("ads query ")
            print(ads_query_rand)
            main_click_one_step(args=args,queries=queries_list,ads_query=ads_query_rand)

            # Başlangıç indeksini güncelle
            start_index = end_index
    
if __name__ == "__main__":
    main()
