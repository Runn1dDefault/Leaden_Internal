import logging
from typing import Optional
from urllib.parse import urlparse
from xml.etree import ElementTree

from django.conf import settings
from django.core.cache import caches

from drivers import SlackDriver
from fetcher import Fetcher
from converters.text_cleaner import TextCleaner
from converters.time_converter import TimeConverter


logger = logging.getLogger('leadgen_management')


class XmlScraper(TimeConverter, TextCleaner, Fetcher):

    def __init__(self, current_timezone: str = "Europe/Kiev"):
        self.timezone = current_timezone
        self.symbols_to_clean = settings.TEXT_TO_CLEAN['projects']['xml_symbols_to_clean']
        self.fields_to_replace = settings.TEXT_TO_CLEAN['projects']['xml_fields_to_replace']

    def scrap_and_parse_projects(self, feed_url: str, keyword: str) -> list[dict] | None:
        slack_driver = SlackDriver()
        parsed_url = urlparse(feed_url)

        if not parsed_url.scheme or 'upwork.com' not in parsed_url.netloc:
            cache = caches[settings.PROJECTS_NOTIFICATION_CACHE]
            slack_driver.save_notification_to_cache(
                notification_cache=cache,
                level='warning',
                msg_header='Feed URL validation error',
                message='<%s|%s>' % (feed_url, keyword)
            )
            return

        if not parsed_url.path.endswith('atom'):
            cache = caches[settings.PROJECTS_NOTIFICATION_CACHE]
            slack_driver.save_notification_to_cache(
                notification_cache=cache,
                level='warning',
                msg_header='This Feed URL\'s must contains `atom`',
                message='<%s|%s>' % (feed_url, keyword)
            )
            return

        data = self.get_xml(
            max_retries=settings.MAX_RETRIES,
            feed_url=feed_url,
            keyword=keyword,
            headers=settings.HEADERS
        )
        if data.get('xml'):
            try:
                new_projects = self._get_projects_from_xml(data=data)
                return new_projects
            except Exception as ex:
                logger.error(f"Error while trying to scrap xml. {ex}")

        logger.error(f"Http response error. {data['error']}")
        logger.error(f"ERROR while trying to fetch projects from atom url.")

        cache = caches[settings.PROJECTS_NOTIFICATION_CACHE]
        slack_driver.save_notification_to_cache(
            notification_cache=cache,
            level='warning',
            msg_header='Something went wrong with getting data for keywords:',
            message='<%s|%s>' % (feed_url, keyword)
        )

    def _get_projects_from_xml(self, data: dict) -> list[dict]:
        xml_projects = list()
        shift = self._get_shift()
        tree = ElementTree.fromstring(data['xml'])

        for entry in tree.findall('{http://www.w3.org/2005/Atom}entry'):
            url = entry.find("{http://www.w3.org/2005/Atom}id").text
            title = entry.find("{http://www.w3.org/2005/Atom}title").text
            summary = entry.find("{http://www.w3.org/2005/Atom}summary").text
            summary_dict = self.parse_summary(summary=summary)

            project = dict(
                shift=shift,
                url=url,
                title=self.clear_string(
                    string_to_clean=title,
                    symbols_to_clean=self.symbols_to_clean
                ),
                description=self.clear_string(
                    string_to_clean=summary_dict['description'],
                    symbols_to_clean=self.symbols_to_clean
                ),
                budget=self.get_number_from_string(
                    string_to_parse=summary_dict.get('budget')
                ),
                hourly=self._parse_hourly_range(
                    string_to_parse=summary_dict.get('hourly_range')
                ),
                category=self.clear_string(
                    string_to_clean=summary_dict['category'],
                    symbols_to_clean=self.symbols_to_clean
                ),
                country=self.clear_string(
                    string_to_clean=summary_dict['country'],
                    symbols_to_clean=self.symbols_to_clean
                ),
                project_type=summary_dict.get('project_type'),
                keyword=data['keyword'],
            )
            xml_projects.append(project)
        return xml_projects

    def parse_summary(self, summary: str) -> dict:

        summary_dict = dict()
        if settings.SUMMARY_TAGS['hourly_range'] in summary:
            payment_type = "hourly_range"
        elif settings.SUMMARY_TAGS['budget'] in summary:
            payment_type = "budget"
        else:
            payment_type = None

        summary_dict['description'], summary = self._get_description(
            stoping_field=payment_type,
            summary=summary
        )

        summary_dict['project_type'] = "hourly"
        if payment_type:
            summary_dict[payment_type] = summary[:summary.find(settings.SUMMARY_TAGS['posted_on'])]
            if payment_type == "budget":
                summary_dict['project_type'] = "fixed"

        summary_dict['category'] = self._get_category(summary=summary)
        summary_dict['country'] = self._get_country(summary=summary)
        return summary_dict

    @staticmethod
    def _get_description(summary: str, stoping_field: str) -> tuple:
        if not stoping_field:
            stoping_field = "posted_on"
        description = summary[:summary.find(settings.SUMMARY_TAGS[stoping_field])]
        summary = summary[summary.find(settings.SUMMARY_TAGS[stoping_field]):]
        return description, summary

    def _get_category(self, summary: str) -> str:
        category = summary[summary.find("<b>Category</b>"):summary.find("<b>Skills</b>")]
        return self.replace_field_from_string(
            string_to_clean=category,
            fields_to_replace=self.fields_to_replace)

    def _get_country(self, summary: str) -> str:
        country = summary[summary.find("<b>Country</b>"):summary.find("<a href")]
        return self.replace_field_from_string(
            string_to_clean=country,
            fields_to_replace=self.fields_to_replace)

    def _parse_hourly_range(self, string_to_parse: Optional[str]) -> Optional[float]:
        if string_to_parse:
            if string_to_parse.count("$") == 2:
                string_to_parse = string_to_parse.split("-")[1]
            return self.get_number_from_string(string_to_parse=string_to_parse)

    def _get_shift(self) -> str:
        current_hour = self.get_timezone_time(timezone=self.timezone).hour
        if current_hour < 4:
            return "0-4"
        elif current_hour < 8:
            return "4-8"
        elif current_hour < 16:
            return "8-16"
        else:
            return "16-24"
