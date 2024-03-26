import json
import time
from urllib import parse

import aiohttp
from pytube import Search
from pytube.innertube import InnerTube, _client_id, _client_secret

from common import get_logger

logger = get_logger()


async def async_is_available_video(running_time, limit_video_length):
    # Live Video
    if running_time is None:
        return False

    if limit_video_length < 0:
        return True

    i = 0
    run_sec = 0
    for sec in reversed(running_time.split(':')):
        run_sec += int(sec) * 60 ** i
        i += 1

    return not (run_sec > limit_video_length)

def is_available_video(running_time, limit_video_length):
    # Live Video
    if running_time is None:
        return False

    if limit_video_length < 0:
        return True

    i = 0
    run_sec = 0
    for sec in reversed(running_time.split(':')):
        run_sec += int(sec) * 60 ** i
        i += 1

    return not (run_sec > limit_video_length)


async def _execute_async_request(
        url, headers=None, data=None,
        timeout=3
):
    start_time = time.time()
    base_headers = {"User-Agent": "Mozilla/5.0", "accept-language": "en-US,en"}
    if headers:
        base_headers.update(headers)
    if data:
        # encode data for request
        if not isinstance(data, bytes):
            data = bytes(json.dumps(data), encoding="utf-8")

    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=url, headers=base_headers, data=data,
                timeout=timeout
        ) as response:
            return await response.json()


def search_videos(query, rows=10, limit_video_length=-1):
    return YoutubeSearch(query, rows, limit_video_length).results


async def async_search_videos(query, rows=10, limit_video_length=-1):
    search_results = await AsyncYoutubeSearch(query, rows, limit_video_length).results
    return search_results


class AsyncYoutubeSearch(Search):
    def __init__(self, query, rows, limit_video_length):
        super().__init__(query)
        self.rows = rows
        self.limit_video_length = limit_video_length
        self._innertube_client = AsyncInnerTube(client='WEB')

    @property
    async def results(self): 
        """Return search results.

        On first call, will generate and return the first set of results.
        Additional results can be generated using ``.get_next_results()``.

        :rtype: list
        :returns:
            A list of YouTube objects.
        """

        if self._results:
            return self._results

        videos, continuation = await self.fetch_and_parse()
        self._results = videos
        self._current_continuation = continuation
        return self._results

    async def fetch_and_parse(self, continuation=None):
        """Fetch from the innertube API and parse the results.

        :param str continuation:
            Continuation string for fetching results.
        :rtype: tuple
        :returns:
            A tuple of a list of YouTube objects and a continuation string.
        """
        # Begin by executing the query and identifying the relevant sections
        #  of the results
        raw_results = await self.fetch_query(continuation)

        # Initial result is handled by try block, continuations by except block
        try:
            sections = raw_results['contents']['twoColumnSearchResultsRenderer'][
                'primaryContents']['sectionListRenderer']['contents']
        except KeyError:
            sections = raw_results['onResponseReceivedCommands'][0][
                'appendContinuationItemsAction']['continuationItems']
        item_renderer = None
        continuation_renderer = None
        for s in sections:
            if 'itemSectionRenderer' in s:
                item_renderer = s['itemSectionRenderer']
            if 'continuationItemRenderer' in s:
                continuation_renderer = s['continuationItemRenderer']

        # If the continuationItemRenderer doesn't exist, assume no further results
        if continuation_renderer:
            next_continuation = continuation_renderer['continuationEndpoint'][
                'continuationCommand']['token']
        else:
            next_continuation = None

        # If the itemSectionRenderer doesn't exist, assume no results.
        if item_renderer:
            videos = []
            raw_video_list = item_renderer['contents']
            for video_details in raw_video_list:
                # Skip over ads
                if video_details.get('searchPyvRenderer', {}).get('ads', None):
                    continue

                # Skip "recommended" type videos e.g. "people also watched" and "popular X"
                #  that break up the search results
                if 'shelfRenderer' in video_details:
                    continue

                # Skip auto-generated "mix" playlist results
                if 'radioRenderer' in video_details:
                    continue

                # Skip playlist results
                if 'playlistRenderer' in video_details:
                    continue

                # Skip channel results
                if 'channelRenderer' in video_details:
                    continue

                # Skip 'people also searched for' results
                if 'horizontalCardListRenderer' in video_details:
                    continue

                # Can't seem to reproduce, probably related to typo fix suggestions
                if 'didYouMeanRenderer' in video_details:
                    continue

                # Seems to be the renderer used for the image shown on a no results page
                if 'backgroundPromoRenderer' in video_details:
                    continue

                if 'videoRenderer' not in video_details:
                    continue

                # Extract relevant video information from the details.
                # Some of this can be used to pre-populate attributes of the
                #  YouTube object.
                vid_renderer = video_details['videoRenderer']
                vid_id = vid_renderer['videoId']
                vid_watch_url = f'https://www.youtube.com/watch?v={vid_id}'
                vid_embed_url = f'https://www.youtube.com/embed/{vid_id}'
                vid_title = vid_renderer['title']['runs'][0]['text']
                vid_author = vid_renderer['ownerText']['runs'][0]['text']
                vid_thumbnail_url = vid_renderer['thumbnail']['thumbnails'][0]['url']

                if 'lengthText' in vid_renderer:
                    vid_length = vid_renderer['lengthText']['simpleText']
                else:
                    vid_length = None

                vid_metadata = {
                    'video_id': vid_id,
                    'video_title': vid_title,
                    'watch_url': vid_watch_url,
                    'embed_url': vid_embed_url,
                    'author': vid_author,
                    'running_time': vid_length,
                    'thumbnail_url': vid_thumbnail_url
                }

                if await async_is_available_video(vid_length, self.limit_video_length):
                    videos.append(vid_metadata)

                if len(videos) >= self.rows:
                    break
        else:
            videos = None

        return videos, next_continuation

    async def fetch_query(self, continuation=None):
        """Fetch raw results from the innertube API.

        :param str continuation:
            Continuation string for fetching results.
        :rtype: dict
        :returns:
            The raw json object returned by the innertube API.
        """
        query_results = await self._innertube_client.search(self.query, continuation)
        if not self._initial_results:
            self._initial_results = query_results
        return query_results  # noqa:R504


class AsyncInnerTube(InnerTube):
    async def search(self, search_query, continuation=None):
        """Make a request to the search endpoint.

        :param str search_query:
            The query to search.
        :rtype: dict
        :returns:
            Raw search query results.
        """
        endpoint = f'{self.base_url}/search'
        query = {
            'query': search_query
        }
        query.update(self.base_params)
        data = {}
        if continuation:
            data['continuation'] = continuation
        data.update(self.base_data)
        return await self._call_api(endpoint, query, data)

    async def _call_api(self, endpoint, query, data):
        """Make a request to a given endpoint with the provided query parameters and data."""
        # Remove the API key if oauth is being used.
        if self.use_oauth:
            del query['key']

        endpoint_url = f'{endpoint}?{parse.urlencode(query)}'
        headers = {
            'Content-Type': 'application/json',
        }
        # Add the bearer token if applicable
        if self.use_oauth:
            if self.access_token:
                await self.refresh_bearer_token()
                headers['Authorization'] = f'Bearer {self.access_token}'
            else:
                await self.fetch_bearer_token()
                headers['Authorization'] = f'Bearer {self.access_token}'

        headers.update(self.header)

        return await _execute_async_request(
            endpoint_url,
            headers=headers,
            data=data
        )

    async def fetch_bearer_token(self):
        """Fetch an OAuth token."""
        # Subtracting 30 seconds is arbitrary to avoid potential time discrepencies
        start_time = int(time.time() - 30)
        data = {
            'client_id': _client_id,
            'scope': 'https://www.googleapis.com/auth/youtube'
        }
        response = await _execute_async_request(
            url='https://oauth2.googleapis.com/device/code',
            headers={
                'Content-Type': 'application/json'
            },
            data=data
        )
        response_data = json.loads(response)
        verification_url = response_data['verification_url']
        user_code = response_data['user_code']
        print(f'Please open {verification_url} and input code {user_code}')
        input('Press enter when you have completed this step.')

        data = {
            'client_id': _client_id,
            'client_secret': _client_secret,
            'device_code': response_data['device_code'],
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
        }
        response = await _execute_async_request(
            url='https://oauth2.googleapis.com/token',
            headers={
                'Content-Type': 'application/json'
            },
            data=data
        )
        response_data = json.loads(response)

        self.access_token = response_data['access_token']
        self.refresh_token = response_data['refresh_token']
        self.expires = start_time + response_data['expires_in']
        self.cache_tokens()

    async def refresh_bearer_token(self, force=False):
        """Refreshes the OAuth token if necessary.

        :param bool force:
            Force-refresh the bearer token.
        """
        if not self.use_oauth:
            return
        # Skip refresh if it's not necessary and not forced
        if self.expires > time.time() and not force:
            return

        # Subtracting 30 seconds is arbitrary to avoid potential time discrepencies
        start_time = int(time.time() - 30)
        data = {
            'client_id': _client_id,
            'client_secret': _client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }

        response = await _execute_async_request(
            'https://oauth2.googleapis.com/token',
            headers={
                'Content-Type': 'application/json'
            },
            data=data
        )

        response_data = json.loads(response)

        self.access_token = response_data['access_token']
        self.expires = start_time + response_data['expires_in']
        self.cache_tokens()


class YoutubeSearch(Search):
    def __init__(self, query, rows, limit_video_length):
        super().__init__(query)
        self.rows = rows
        self.limit_video_length = limit_video_length
        self._innertube_client = InnerTube(client='WEB')

    @property
    def results(self):
        """Return search results.

        On first call, will generate and return the first set of results.
        Additional results can be generated using ``.get_next_results()``.

        :rtype: list
        :returns:
            A list of YouTube objects.
        """

        if self._results:
            return self._results

        videos, continuation = self.fetch_and_parse()
        self._results = videos
        self._current_continuation = continuation
        return self._results

    def fetch_and_parse(self, continuation=None):
        """Fetch from the innertube API and parse the results.

        :param str continuation:
            Continuation string for fetching results.
        :rtype: tuple
        :returns:
            A tuple of a list of YouTube objects and a continuation string.
        """
        # Begin by executing the query and identifying the relevant sections
        #  of the results
        raw_results = self.fetch_query(continuation)

        # Initial result is handled by try block, continuations by except block
        try:
            sections = raw_results['contents']['twoColumnSearchResultsRenderer'][
                'primaryContents']['sectionListRenderer']['contents']
        except KeyError:
            sections = raw_results['onResponseReceivedCommands'][0][
                'appendContinuationItemsAction']['continuationItems']
        item_renderer = None
        continuation_renderer = None
        for s in sections:
            if 'itemSectionRenderer' in s:
                item_renderer = s['itemSectionRenderer']
            if 'continuationItemRenderer' in s:
                continuation_renderer = s['continuationItemRenderer']

        # If the continuationItemRenderer doesn't exist, assume no further results
        if continuation_renderer:
            next_continuation = continuation_renderer['continuationEndpoint'][
                'continuationCommand']['token']
        else:
            next_continuation = None

        # If the itemSectionRenderer doesn't exist, assume no results.
        if item_renderer:
            videos = []
            raw_video_list = item_renderer['contents']
            for video_details in raw_video_list:
                # Skip over ads
                if video_details.get('searchPyvRenderer', {}).get('ads', None):
                    continue

                # Skip "recommended" type videos e.g. "people also watched" and "popular X"
                #  that break up the search results
                if 'shelfRenderer' in video_details:
                    continue

                # Skip auto-generated "mix" playlist results
                if 'radioRenderer' in video_details:
                    continue

                # Skip playlist results
                if 'playlistRenderer' in video_details:
                    continue

                # Skip channel results
                if 'channelRenderer' in video_details:
                    continue

                # Skip 'people also searched for' results
                if 'horizontalCardListRenderer' in video_details:
                    continue

                # Can't seem to reproduce, probably related to typo fix suggestions
                if 'didYouMeanRenderer' in video_details:
                    continue

                # Seems to be the renderer used for the image shown on a no results page
                if 'backgroundPromoRenderer' in video_details:
                    continue

                if 'videoRenderer' not in video_details:
                    continue

                # Extract relevant video information from the details.
                # Some of this can be used to pre-populate attributes of the
                #  YouTube object.
                vid_renderer = video_details['videoRenderer']
                vid_id = vid_renderer['videoId']
                vid_watch_url = f'https://www.youtube.com/watch?v={vid_id}'
                vid_embed_url = f'https://www.youtube.com/embed/{vid_id}'
                vid_title = vid_renderer['title']['runs'][0]['text']
                vid_author = vid_renderer['ownerText']['runs'][0]['text']
                vid_thumbnail_url = vid_renderer['thumbnail']['thumbnails'][0]['url']

                if 'lengthText' in vid_renderer:
                    vid_length = vid_renderer['lengthText']['simpleText']
                else:
                    vid_length = None

                vid_metadata = {
                    'video_id': vid_id,
                    'video_title': vid_title,
                    'watch_url': vid_watch_url,
                    'embed_url': vid_embed_url,
                    'author': vid_author,
                    'running_time': vid_length,
                    'thumbnail_url': vid_thumbnail_url
                }

                if is_available_video(vid_length, self.limit_video_length):
                    videos.append(vid_metadata)

                if len(videos) >= self.rows:
                    break
        else:
            videos = None

        return videos, next_continuation
