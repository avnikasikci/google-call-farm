import subprocess
import time
from logger import logger
import traceback

def main() -> None:

    while True:
        process = subprocess.Popen(["python", "run_multi_ad_clicker.py"])
        try:
            process.wait()  # Program kapanana kadar bekler
        except KeyboardInterrupt:
            print("Kapatma isteği alındı, çıkılıyor...")
            process.terminate()
            break  # Döngüyü kır ve çık
        print("Program kapandı, tekrar başlatılıyor...")
        time.sleep(2)


if __name__ == "__main__":

    try:
        print("Multi browser kapanınca tekrar açılacak.")
        main()
    except Exception as exp:
        logger.error("Exception occurred. See the details in the log file.")

        message = str(exp).split("\n")[0]
        logger.debug(f"Exception: {message}")
        details = traceback.format_tb(exp.__traceback__)
        logger.debug(f"Exception details: \n{''.join(details)}")
