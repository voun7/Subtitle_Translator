import html
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from time import perf_counter

import deepl
import requests

logger = logging.getLogger(__name__)

# Do not log this messages unless they are at least warnings
logging.getLogger("deepl").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class Deepl:
    credential_file = Path()

    def __init__(self, source_lang: str, target_lang: str) -> None:
        self.source_lang, self.target_lang = self.parse_lang(source_lang), self.parse_lang(target_lang)
        auth_key = self.credential_file.read_text()
        self.translator = deepl.Translator(auth_key) if auth_key else None
        self.unwanted_pattern = re.compile(r"\(.+?\)")

    @staticmethod
    def parse_lang(lang: str) -> str:
        if lang == "en":
            lang = "EN-US"
        elif lang == "ch":
            lang = "ZH"
        return lang

    def __call__(self, text: str) -> str:
        """
        This method calls and uses the deepl translation API to translate text.
        """
        translation = self.translator.translate_text(text, source_lang=self.source_lang,
                                                     target_lang=self.target_lang).text
        if self.unwanted_pattern.search(translation) or "lit." in translation or "fig." in translation:
            translation2 = self.translator.translate_text(f"{text.strip()}.", source_lang=self.source_lang,
                                                          target_lang=self.target_lang).text
            logger.info(f"Retranslation for text: {translation}, New translation: {translation2}")
            translation = translation2
        return translation

    def usage(self) -> None:
        """
        This method prints the overall state of the api usage.
        """
        if not self.translator:
            return
        usage = self.translator.get_usage()
        if usage.any_limit_reached:
            logger.warning("Deepl Translation limit reached.")
        if usage.character.valid:
            logger.info(f"Deepl Character usage: {usage.character.count:,} of {usage.character.limit:,}")
        if usage.document.valid:
            logger.info(f"Document usage: {usage.document.count} of {usage.document.limit}")

    def limit_reached(self) -> bool:
        """
        This method checks if the api limit usage has been reached.
        """
        usage = self.translator.get_usage()
        char_limit = usage.character.limit - 10
        return usage.any_limit_reached or usage.character.count > char_limit


class GoogleTrans:
    credential_file = Path()
    url = "https://translation.googleapis.com/language/translate/v2"

    def __init__(self, source_lang: str, target_lang: str) -> None:
        self.source_lang, self.target_lang = self.parse_lang(source_lang), self.parse_lang(target_lang)
        auth_key = self.credential_file.read_text()
        self.session = requests.Session() if auth_key else None
        self.params = {"source": self.source_lang, "target": self.target_lang, "key": auth_key}

    @staticmethod
    def parse_lang(lang: str) -> str:
        if lang == "ch":
            lang = "zh"
        return lang

    def __call__(self, text: str) -> str:
        """
        This method calls and uses the Google cloud translation API to translate text.
        """
        response = self.session.get(self.url, params={"q": text} | self.params)
        translated_text = response.json()["data"]["translations"][0]["translatedText"]
        return html.unescape(translated_text)


class SubTranslator:
    def __init__(self, sub_dir: Path, source_lang: str, target_lang: str) -> None:
        self.sub_dir, self.new_suffix = sub_dir, f".{target_lang}.srt".lower()
        self.txt_pattern = re.compile(r"[a-zA-z\u4e00-\u9fff]+")
        self.deepl_translator = Deepl(source_lang, target_lang)
        self.google_translator = GoogleTrans(source_lang, target_lang)

    def new_subbed_file(self, file: Path, lines: list) -> None:
        """
        This method creates a new srt file with the new suffix and writes the lines with translated text into it.
        """
        new_name = file.with_suffix(self.new_suffix)
        logger.info(f"New file created Name: {new_name}")
        with open(new_name, "w", encoding="utf-8") as new_sub:
            new_sub.writelines(lines)

    def translate_subtitle(self, sub_file: Path) -> None:
        """
        This method reads a subtitle file and sends the lines with text that contain at least one or more English
        letters or CJK Unified Ideographs to be translated and written into a new file.
        """
        logger.info(f"Starting translation for file: {sub_file.name}, New suffix: {self.new_suffix}")
        if self.deepl_translator.translator and not self.deepl_translator.limit_reached():
            trans_name, trans_fn = "deepl", self.deepl_translator
        else:
            trans_name, trans_fn = "google", self.google_translator

        with open(sub_file, encoding="utf8") as sub:
            lines = []
            for line in sub:
                if self.txt_pattern.search(line):
                    translated_line = trans_fn(line)
                    translated_line = translated_line if translated_line.endswith("\n") else f"{translated_line}\n"
                    print(f"{line}--translated with {trans_name} to--\n{translated_line}")
                    lines.append(translated_line)
                else:
                    lines.append(line)
            self.new_subbed_file(sub_file, lines)

    def translate_sub_files(self, max_processes: int) -> None:
        """
        This method looks for the srt files in the folder and translates them with multithreading.
        Subtitle files that have the new suffix in name will not be translated.
        :param max_processes: The max number of translation processes that can take place at a time.
        """
        self.deepl_translator.usage()
        sub_files = [file for file in self.sub_dir.glob("*.srt") if self.new_suffix not in file.name]
        if not len(sub_files):
            logger.info("No srt file to be translated was found!")
            return
        start_time = perf_counter()
        with ThreadPoolExecutor(max_processes) as executor:
            futures = [executor.submit(self.translate_subtitle, sub_file) for sub_file in sub_files]
            for future in futures:
                if error := future.exception():
                    logger.error(f"\n{error}\n")
        logger.info(f"Translations Duration: {timedelta(seconds=round(perf_counter() - start_time))}")
        self.deepl_translator.usage()
        logger.info("All Translations done!\n")
