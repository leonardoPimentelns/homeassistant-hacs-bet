
"""Platform for sensor integration."""
from __future__ import annotations

from datetime import datetime,timedelta,timezone
import logging
import voluptuous
import json
from requests.structures import CaseInsensitiveDict
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from homeassistant import const
from homeassistant.helpers import entity
from homeassistant import util
from homeassistant.helpers import config_validation
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import time

_LOGGER = logging.getLogger(__name__)

UPDATE_FREQUENCY = timedelta(seconds=1)

# PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
#     {
        
#         vol.Required(LEAGUE): vol.All(cv.ensure_list, [cv.string]),
#         vol.Required(NAME): cv.string,
        
#     }
# )
def setup_platform(
    hass,
    config,
    add_entities,
    discovery_info
):
    """Set up the Bet sensors."""
    
    
    add_entities([BetMineSensor(config,hass)],True)


class BetMineSensor(entity.Entity):
    """Representation of a Espn sensor."""

    def __init__(self,config,hass):
        """Initialize a new BetMine sensor."""
        self.config = config
        self._attr_name =  'Bet'
        self.hass = hass
        self.event = None
        self.matches= []
        self.times = []
       


    @property
    def icon(self):
        """Return icon."""
        return "mdi:soccer"


    @util.Throttle(UPDATE_FREQUENCY)
    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
       
        
        self.matches = get_matches()
        


    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        self._attributes = {
        
            "events": self.matches,

        }
        return  self._attributes


def get_score():
    fixId = []
    url = "https://api.betmines.com/betmines/v1/fixtures/livescores"
    resp = requests.get(url)
    data = resp.json()

    for item in data:
        if 'events' in item and item['events']['data']:
            localTeam = item['localTeam']['data']['name']
            visitorTeam = item['visitorTeam']['data']['name']
            scores = item['scores']
            localTeamScore = item['scores']["localTeamScore"]
            visitorTeamScore = item['scores']["visitorTeamScore"]
            ftScore = item['scores'].get("ftScore")
            htScore = item['scores'].get("htScore")

            fixId.append({
                "fixtureId": item['events']['data'][0]['fixtureId'],
                "teams": f'{localTeam} {localTeamScore} x {visitorTeamScore} {visitorTeam}',
                "scores": {"htScore": htScore, "ftScore": ftScore}
            })

    return fixId


def get_matches():
    fixId = []

    today = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"https://api.betmines.com/betmines/v1/fixtures/web?dateFormat=extended&platform=website&from={today}&to={tomorrow}"
    resp = requests.get(url)
    data = resp.json()
   
    score_info = get_score()

    for item in data:
        matche_time = date_time(item['dateTime'])
        league_name = item['league']['name']
        local_team = item['localTeam']
        visitor_team = item['visitorTeam']
        local_team_position = item.get('localTeamPosition')
        visitor_team_position = item.get('visitorTeamPosition')
        local_team_score = item['localTeamScore']
        visitor_team_score = item.get('visitorTeamScore')

        probability = item.get('probability')

        if probability and probability.get('fixutreId') is not None:
            fixtureId = probability.get('fixutreId')

        htScore = None
        ftScore = None
        for score_item in score_info:
            if score_item['fixtureId'] == fixtureId:
                htScore = score_item['scores'].get('htScore')
                ftScore = score_item['scores'].get('ftScore')
                break

        probabilitys = []

        if probability is not None:
            filtered_values = {key: value for key, value in probability.items() if key in ["over_1_5", "over_2_5", "over_3_5", "btts"]}
            
            btts_probability = None
            if 'btts' in filtered_values:
                btts_probability = True if local_team_score > 0 and visitor_team_score > 0 else False

            formatted_probabilitys = {key: str(value) for key, value in filtered_values.items()}

            fixId.append({
                'dateTime':matche_time,
                'league': league_name,
                'minute': item.get('minute'),
                'timeStatus': item['timeStatus'],
                'htScore': htScore,
                'ftScore': ftScore,
                'fixtureId': fixtureId,
                'localTeam': {
                    'id': local_team['id'],
                    'logoPath': local_team.get('logoPath'),
                    'name': local_team['name'],
                    'Position': local_team_position,
                    'Score': local_team_score
                },
                'visitorTeam': {
                    'id': visitor_team['id'],
                    'logoPath': visitor_team.get('logoPath'),
                    'name': visitor_team['name'],
                    'Position': visitor_team_position,
                    'Score': visitor_team_score
                },
                'probability': {"btts": btts_probability, "filtered_values": formatted_probabilitys}
            })

    return fixId


def date_time(data_hora_utc):
   
    data_hora_utc = datetime.strptime(data_hora_utc, "%Y-%m-%dT%H:%M:%SZ")
   
    diferenca_utc_brt = timedelta(hours=-3)
    data_hora_brt = data_hora_utc + diferenca_utc_brt


    data_hora_brt_formatada = data_hora_brt.strftime("%Y-%m-%d %H:%M:%S")
    return data_hora_brt_formatada


