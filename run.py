import logging
from pathlib import Path
from fortune_radar.bot import RadarBot
from fortune_radar.config import load_settings

def main():
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings=load_settings(Path(__file__).resolve().parent); RadarBot(settings).run(settings.token,log_handler=None)
if __name__=="__main__":main()
