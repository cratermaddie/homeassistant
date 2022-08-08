"""Support for getting data from websites with scraping."""
import logging
import re

from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import voluptuous as vol

from homeassistant.components.rest.data import RestData
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_HEADERS,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_RESOURCE,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    HTTP_BASIC_AUTHENTICATION,
    HTTP_DIGEST_AUTHENTICATION,
)
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

CONF_SELECT = "select"
CONF_INDEX = "index"

DEFAULT_NAME = "MV scrape"
DEFAULT_VERIFY_SSL = True
DEFAULT_RESOURCE = "https://www.manyvids.com/View-my-earnings/"
DEFAULT_SELECT = "div.form-style.earnings.mv-controls"
DEFAULT_UNIT_OF_MEASUREMENT = "$"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_RESOURCE, default=DEFAULT_RESOURCE): cv.string,
        vol.Optional(CONF_SELECT, default=DEFAULT_SELECT): cv.string,
        vol.Optional(CONF_INDEX, default=0): cv.positive_int,
        vol.Optional(CONF_AUTHENTICATION): vol.In(
            [HTTP_BASIC_AUTHENTICATION, HTTP_DIGEST_AUTHENTICATION]
        ),
        vol.Optional(CONF_HEADERS): vol.Schema({cv.string: cv.string}),
        vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=DEFAULT_UNIT_OF_MEASUREMENT): cv.string,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Web scrape sensor."""
    name = config.get(CONF_NAME)
    resource = config.get(CONF_RESOURCE)
    method = "GET"
#    payload = None
    params = None
    data = None
    headers = config.get(CONF_HEADERS)
    verify_ssl = config.get(CONF_VERIFY_SSL)
    select = config.get(CONF_SELECT)
    index = config.get(CONF_INDEX)
    unit = config.get(CONF_UNIT_OF_MEASUREMENT)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    if username and password:
        if config.get(CONF_AUTHENTICATION) == HTTP_DIGEST_AUTHENTICATION:
            auth = HTTPDigestAuth(username, password)
        else:
            auth = HTTPBasicAuth(username, password)
    else:
        auth = None
#    rest = RestData(method, resource, auth, headers, payload, verify_ssl)
    rest = RestData(hass, method, resource, auth, headers, params, data, verify_ssl)
    rest.async_update()

    if rest.data is None:
        raise PlatformNotReady

    add_entities(
        [ScrapeSensor(hass, rest, name, select, index, unit)]
    )
    return True


class ScrapeSensor(Entity):
    """Representation of a web scrape sensor."""

    def __init__(self, hass, rest, name, select, index, unit):
        """Initialize a web scrape sensor."""
        self._hass = hass
        self.rest = rest
        self._name = name
        self._state = None
        self._table = None
        self._table_selector = select
        self._token_balance_tokens = None
        self._token_balance_dollars = None
        self._token_selector = "div.card-header.row>span.col-md-2.col-3"
        self._daily_rank = None
        self._daily_rank_selector = "span.col-md-7.col-5.ellipsis"
        self._monthly_rank = None
        self._monthly_rank_selector = "span.col-md-7.col-5.ellipsis"
        self._next_pay = None
        self._next_pay_selector = "span.current-pay-total"
        self._monthly_sales = None
        self._monthly_sales_selector = "span.this-month-sales"
        self._index = index
        self._unit_of_measurement = unit


    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def token_balance_tokens(self):
        """Return token_balance_tokens."""
        return self._token_balance_tokens

    @property
    def token_balance_dollars(self):
        """Return token_balance_dollars."""
        return self._token_balance_dollars

    @property
    def daily_rank(self):
        """Return daily_rank."""
        return self._daily_rank

    @property
    def monthly_rank(self):
        """Return monthly_rank."""
        return self._monthly_rank

    @property
    def next_pay(self):
        """Return next_pay."""
        return self._next_pay

    @property
    def monthly_sales(self):
        """Return monthly_sales."""
        return self._monthly_sales

    @property
    def table(self):
        """Return table."""
        return self._table

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            'token_balance_dollars': self._token_balance_dollars,
            'token_balance_tokens': self._token_balance_tokens,
            'daily_rank': self._daily_rank,
            'monthly_rank': self._monthly_rank,
            'next_pay': self._next_pay,
            'monthly_sales': self._monthly_sales,
            'table': self._table,
        }

    def update(self):
        """Get the latest data from the source and updates the state."""
        self.rest.async_update()
        if self.rest.data is None:
            _LOGGER.error("Unable to retrieve data")
            return

        raw_data = BeautifulSoup(self.rest.data, "html.parser")
        _LOGGER.debug(raw_data)

        try:
            token_balance_value = raw_data.select(self._token_selector)[self._index].text
            token_balance_tokens_match = re.search("^\d+", token_balance_value)
            token_balance_dollars_match = re.search("\d{1,2}.\d{1,2}", token_balance_value)

            self._token_balance_tokens = token_balance_tokens_match.group(0)
            self._token_balance_dollars = token_balance_dollars_match.group(0)
            _LOGGER.debug(token_balance_value)
        except IndexError:
            _LOGGER.error("Unable to extract token balance from HTML")
            self._token_balance = None

        try:
            daily_rank_value = raw_data.select(self._daily_rank_selector)[self._index].text
            daily_rank_match = re.search("(--$)|(\d+$)", daily_rank_value)
            daily_rank_result = daily_rank_match[0]
            if daily_rank_result != "--":
                self._daily_rank = daily_rank_result
            else:
                self._daily_rank = None
#                self._daily_rank = self._hass.states.get("sensor." + self._name.lower().replace(" ","_")).attributes.get('daily_rank')
            _LOGGER.debug(daily_rank_value)
        except IndexError:
            _LOGGER.error("Unable to extract daily rank from HTML")
            self._daily_rank = None

        try:
            monthly_rank_value = raw_data.select(self._monthly_rank_selector)[1].text
            monthly_rank_match = re.search("(--$)|(\d+$)", monthly_rank_value)
            monthly_rank_result = monthly_rank_match[0]
            _LOGGER.debug(monthly_rank_result)
            if monthly_rank_result != "--":
                self._monthly_rank = monthly_rank_result
            else:
                self._monthly_rank = None
#                self._monthly_rank = self._hass.states.get("sensor." + self._name.lower().replace(" ","_")).attributes.get('monthly_rank')
            _LOGGER.debug(monthly_rank_value)
        except IndexError:
            _LOGGER.error("Unable to extract monthly rank from HTML")
            self._monthly_rank = None

        try:
            next_pay_value = raw_data.select(self._next_pay_selector)[self._index].text
            next_pay_match = re.search("\d{1,2}.\d{1,2}", next_pay_value)

            self._next_pay = self._state = next_pay_match.group(0)
            _LOGGER.debug(next_pay_value)
        except IndexError:
            _LOGGER.error("Unable to extract next pay from HTML")
            self._next_pay = None

        try:
            monthly_sales_value = raw_data.select(self._monthly_sales_selector)[self._index].text
            monthly_sales_match = re.search("\d{1,2}.\d{1,2}", monthly_sales_value)

            self._monthly_sales = monthly_sales_match.group(0)
            _LOGGER.debug(monthly_sales_value)
        except IndexError:
            _LOGGER.error("Unable to extract monthly sales from HTML")
            self._monthly_sales = None

        try:
            self._table = raw_data.select(self._table_selector)[self._index].text
            _LOGGER.debug(self._table)
        except IndexError:
            _LOGGER.error("Unable to extract table from HTML")
            self._table = None