import logging
from pathlib import Path

from logger_setup import setup_logging
from translator import Deepl, GoogleTrans, SubTranslator

logger = logging.getLogger(__name__)


def set_credentials() -> None:
    credentials_dir = Path("credentials")
    credentials_dir.mkdir(exist_ok=True)
    deepl_cred_file = credentials_dir / "deepl api key.txt"
    google_cred_file = credentials_dir / "google api key.txt"

    if deepl_cred_file.exists():
        Deepl.credential_file = deepl_cred_file
    else:
        deepl_cred_file.write_text("")

    if google_cred_file.exists():
        GoogleTrans.credential_file = google_cred_file
    else:
        google_cred_file.write_text("")

    if not deepl_cred_file.read_text() and not google_cred_file.read_text():
        logger.info("No Translation API key found. Exiting program..."), exit()


def main() -> None:
    set_credentials()

    translation_dir = Path(r"")
    source_lang, target_lang = "", ""
    assert source_lang and target_lang, "Source and target languages should be provided!"

    sub_trans = SubTranslator(translation_dir, source_lang, target_lang)
    sub_trans.translate_sub_files(6)


if __name__ == "__main__":
    setup_logging()
    logger.debug("Logging Started")
    main()
    logger.debug("Logging Ended\n")
