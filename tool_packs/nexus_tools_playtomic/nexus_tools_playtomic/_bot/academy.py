"""Read-only public academy listings; not private coach availability or courses."""
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
import re
import json
from zoneinfo import ZoneInfo
import requests
from .client import HEADERS, CapabilityUnavailableError, default_config, list_venues, _pace_playtomic_request


class _Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.current = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div':
            if self.current is not None:
                self.depth += 1
            elif attrs.get('data-slot') == 'card':
                self.current = {'text': [], 'url': None, 'title': None}
                self.depth = 1
        if self.current is not None and tag == 'a' and attrs.get('href', '').startswith('/activities/public-classes/'):
            self.current.update(url='https://playtomic.com' + attrs['href'], title=attrs.get('aria-label'))

    def handle_endtag(self, tag):
        if tag == 'div' and self.current is not None:
            self.depth -= 1
            if self.depth == 0:
                if self.current['url']:
                    self.cards.append(self.current)
                self.current = None

    def handle_data(self, data):
        if self.current is not None and data.strip():
            self.current['text'].append(data.strip())


def _parse_cards(html, *, today):
    parser = _Cards()
    parser.feed(html)
    # Next streams some cards as React Flight records instead of HTML tags.
    records = {}
    for match in re.finditer(r'self\.__next_f\.push\((.*?)\)</script>', html):
        try:
            chunk = json.loads(match[1])[1]
        except (ValueError, IndexError, TypeError):
            continue
        for record in re.finditer(r'([0-9a-f]+):(?=[\[{])', chunk):
            try: records[record[1]] = json.JSONDecoder().raw_decode(chunk[record.end():])[0]
            except ValueError: pass
    def walk(value, card, seen):
        if isinstance(value, str):
            ref = value[2:] if value.startswith('$L') else value[1:] if value.startswith('$') else None
            if ref in records and ref not in seen:
                walk(records[ref], card, seen | {ref})
            elif ref is None:
                card['text'].append(value)
        elif isinstance(value, list):
            if len(value) == 4 and value[0] == '$' and isinstance(value[3], dict):
                props = value[3]
                href = props.get('href', '')
                if href.startswith('/activities/public-classes/'):
                    card.update(url='https://playtomic.com'+href, title=props.get('aria-label'))
                walk(props.get('children'), card, seen)
            else:
                for child in value: walk(child, card, seen)
    def find_cards(value):
        if isinstance(value, list):
            if len(value) == 4 and value[0] == '$' and isinstance(value[3], dict) and value[3].get('data-slot') == 'card':
                card = {'text': [], 'url': None, 'title': None}
                walk(value, card, set())
                if card['url']: parser.cards.append(card)
            else:
                for child in value: find_cards(child)
        elif isinstance(value, dict):
            for child in value.values(): find_cards(child)
    for value in records.values(): find_cards(value)
    if not parser.cards:
        # Require an actual rendered empty-state, never translation text in scripts.
        visible = re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.S)
        if 'There are no activities that match the current filters for this club.' not in visible:
            raise CapabilityUnavailableError('Could not read Playtomic public academy listings; page format may have changed.')
    result = []
    seen = set()
    for card in parser.cards:
        if card['url'] in seen:
            continue
        seen.add(card['url'])
        text = ' '.join(card['text'])
        match = re.search(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), ([A-Za-z]+) (\d{1,2})(?:, (\d{4}))? \| (\d{2}:\d{2})h', text)
        if not match:
            raise CapabilityUnavailableError('Could not parse a public academy session date.')
        _, month, day, year, clock = match.groups()
        # The public listing omits the year. Its upcoming dates roll over at New Year.
        session_day = datetime.strptime(f'{year or today.year} {month} {day}', '%Y %B %d').date()
        if not year and session_day < today - timedelta(days=1):
            session_day = session_day.replace(year=today.year + 1)
        duration = re.search(r'\b(\d+) min\b', text)
        price = re.search(r'£\s*\d+(?:\.\d{2})?', text)
        result.append({'title': card['title'], 'date': session_day.isoformat(), 'start_time': clock,
                       'duration_minutes': int(duration[1]) if duration else None,
                       'price_display': price[0] if price else None, 'url': card['url'],
                       'kind': 'public_class'})
    return result


def get_academy_sessions(*, start_date=None, end_date=None, start_time=None, end_time=None, tenant_ids=None, config=None):
    """Return per-venue public listings and errors, with explicit limited coverage."""
    cfg = config or default_config()
    today = datetime.now(ZoneInfo('Europe/London')).date()
    first = date.fromisoformat(start_date) if start_date else today
    last = date.fromisoformat(end_date) if end_date else first + timedelta(days=6)
    if last < first or (last-first).days >= 14:
        raise ValueError('Academy date range must be between 1 and 14 days.')
    def normal_time(value):
        if value is None: return None
        if not re.fullmatch(r'\d{1,2}:\d{2}', value): raise ValueError('Time must be HH:MM')
        return datetime.strptime(value, '%H:%M').strftime('%H:%M')
    start_time, end_time = normal_time(start_time), normal_time(end_time)
    if start_time and end_time and start_time > end_time:
        raise ValueError('End time must not precede start time')
    venues = list_venues(config=cfg)
    if tenant_ids:
        wanted = set(tenant_ids)
        if wanted - {v['tenant_id'] for v in venues}:
            raise ValueError('Unknown academy venue ID')
        venues = [v for v in venues if v['tenant_id'] in wanted]
    results = []
    for venue in venues:
        slug = venue.get('slug') or venue.get('tenant_uid')
        row = {'tenant_id': venue['tenant_id'], 'tenant_name': venue['name'],
               'url': f'https://playtomic.com/clubs/{slug}/academy/public-classes',
               'sessions': [], 'coverage': 'Public upcoming academy listings only; may include socials. Private coaching and courses are not included.'}
        try:
            if not slug or not re.fullmatch(r'[a-z0-9-]+', slug):
                raise CapabilityUnavailableError('Venue has no usable public academy page.')
            _pace_playtomic_request(cfg)
            response = requests.get(row['url'], headers={**HEADERS, 'Accept-Language': 'en-GB,en;q=0.9'}, timeout=cfg.http_timeout_seconds)
            response.raise_for_status()
            sessions = _parse_cards(response.text, today=today)
            row['sessions'] = [s for s in sessions if first.isoformat() <= s['date'] <= last.isoformat()
                               and (not start_time or s['start_time'] >= start_time)
                               and (not end_time or s['start_time'] <= end_time)]
            row['ok'] = True
        except (requests.RequestException, CapabilityUnavailableError, ValueError) as exc:
            row.update(ok=False, error=str(exc))
        results.append(row)
    return results


def format_academy_sessions(rows, *, include_links=True):
    blocks = ['*Public academy sessions* (Europe/London)']
    for row in rows:
        lines = [f"*{row['tenant_name']}*"]
        if not row['ok']:
            lines.append('Academy lookup unavailable: ' + row['error'])
        elif not row['sessions']:
            lines.append('No matching sessions shown in the public academy listing.')
        else:
            for s in row['sessions'][:20]:
                detail = f"{s['date']} {s['start_time']} · {s['title']}"
                if s['duration_minutes']: detail += f" · {s['duration_minutes']}m"
                if s['price_display']: detail += f" · {s['price_display']}"
                lines.append(detail)
                if include_links: lines.append(s['url'])
            if len(row['sessions']) > 20: lines.append(f"Showing 20 of {len(row['sessions'])} sessions; see the club academy page.")
        if include_links: lines.append(row['url'])
        blocks.append('\n'.join(lines))
    blocks.append('Public listings may include socials. Private coach availability and courses are not included.')
    return '\n\n'.join(blocks)
