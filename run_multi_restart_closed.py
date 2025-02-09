import os
import signal
import subprocess
from logger import logger
import traceback

def main() -> None:

    # Çalışan süreçleri listeleyelim
    process_list = subprocess.check_output("ps aux | grep python", shell=True).decode()

    # Kapatmak istediğimiz dosyanın adını belirtiyoruz
    target_script = "run_multi_ad_clicker.py"

    for line in process_list.split("\n"):
        if target_script in line and "grep" not in line:
            pid = int(line.split()[1])  # PID numarasını al
            print(f"{target_script} süreci bulunuyor: PID {pid}, kapatılıyor...")
            os.kill(pid, signal.SIGKILL)  # Süreci öldür

    print(f"{target_script} başarıyla kapatıldı!")



if __name__ == "__main__":

    try:
        print("Multi browser kapatma isteği")
        logger.debug(f"Multi browser kapatma isteğ")

        main()
    except Exception as exp:
        logger.error("Exception occurred. See the details in the log file.")

        message = str(exp).split("\n")[0]
        logger.debug(f"Exception: {message}")
        details = traceback.format_tb(exp.__traceback__)
        logger.debug(f"Exception details: \n{''.join(details)}")
