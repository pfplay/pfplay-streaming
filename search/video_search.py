from pytube import Search

from common import get_logger
from search.config import LIMIT_VIDEO_LENGTH

logger = get_logger()


def is_available_video(running_time):
    # Live Video
    if running_time is None:
        return False

    i = 0
    run_sec = 0
    for sec in reversed(running_time.split(':')):
        run_sec += int(sec) * 60 ** i
        i += 1

    if run_sec > LIMIT_VIDEO_LENGTH:
        return False
    else:
        return True


def search_videos(query, rows=10):
    return YoutubeSearch(query, rows).results


class YoutubeSearch(Search):
    def __init__(self, query, rows):
        super().__init__(query)
        self.rows = rows

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

                if is_available_video(vid_length):
                    videos.append(vid_metadata)

                if len(videos) >= self.rows:
                    break
        else:
            videos = None

        return videos, next_continuation
