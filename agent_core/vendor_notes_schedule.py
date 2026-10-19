"""Deterministic, publication-gated guider-work schedule from crew notes.

Only explicit, readable scheduled hardware work is admitted. Dates are calendar
 dates (flat-test night windows alone roll early hours to the following day).
No model, network, card identity, measured throughput, or hidden events are used.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

GRACE_SECONDS = 180
MAX_REASON_CHARS = 20000
MAX_RECORDS = 4096
MAX_EVENTS = 4096
MAX_REVISIONS = 64
UTC = timezone.utc
_CN = {'零': 0, '〇': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4,
       '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
_NUM = r'[0-9零〇一二两三四五六七八九十]+'
_TRANSLATE = str.maketrans('導機點時兩後遲間報試場燈預當順說聽沒認這與為組會風雲',
                          '导机点时两后迟间报试场灯预当顺说听没认这与为组会风云')
_DATE = re.compile(r'(?<![\d/])(\d{1,2})\s*/\s*(\d{1,2})(?![\d/])|(' + _NUM + r')月(' + _NUM + r')日')
_CLOCK = re.compile(r'(?<!\d)(\d{1,2})\s*:\s*(\d{2})(?!\d)|(' + _NUM + r')[点时](?:半|一刻|三刻|整|(' + _NUM + r')分?)?')
_CAMERA = re.compile(r'导星相机|ガイダーカメラ|ガイドカメラ|guider\s+camera', re.I)
_FLAT = re.compile(r'平场|镜盖|フラット|flat[ -]?(?:lamp|test)|mirror[ -]cap', re.I)
_RUMOR = re.compile(r'听说|传言|谣言|传闻|据说|尚待核实|未经确认|未核实|没确认|未确认|没见正式|没有正式|先别|别当真|うわさ|未確認|聞いた話|rumou?r|unconfirmed|unverified|hearsay', re.I)
_NEIGHBOR = re.compile(r'隔壁|隣の|邻.{0,3}观测|別の山|别的山|另一座天文台|本站无关|他站|他の望遠鏡|neighbor|another observatory|other telescope', re.I)
_OBSOLETE = re.compile(r'旧通知|过期通知|仅作存档|历史记录|旧版通知|以前の通知|obsolete|superseded|archive only', re.I)
_UNCERTAIN = re.compile(r'[?？]|对吗|对吧|是吧|没错吧|没记错|记得|好像|会不会|该不会|不是.{0,30}吗|是不是|才对吧|那次.{0,30}[吗吧]|这个时间吧')
_CORRECTION = re.compile(r'更正|有误|(?:记|搞|弄)错(?:了|的)|记岔了|记混了|搞混了|correction|corrected', re.I)
_CANCEL = re.compile(r'取消|不会动|中止|撤销|撤回|(?:作业|计划|通知).{0,4}作废|取りやめ|called\s+off|withdrawn|cancel', re.I)
# A negated work statement ("不要动导星相机，照常观测") announces no work: it is read as a cancellation of that time.
_NEGATED = re.compile(r'(?:不要|不用|不必|无需|不需要|别|勿|不再|没有|并不|不)\s*(?:再\s*)?(?:去\s*)?(?:动|碰|拆|调|换|修|弄)'
                      r'\s*(?:一下\s*)?(?:那台\s*|这台\s*)?(?:导星相机|ガイダーカメラ)'
                      r'|(?:导星相机|ガイダーカメラ).{0,8}?(?:不动|不用动|不需要动|别动|不要动|不碰|照常|没有作业|没作业)'
                      r'|(?:do\s+not|don\'t|won\'t|will\s+not|no\s+need\s+to)\s+(?:touch|work\s+on|service|move)\s+the\s+guider'
                      r'|no\s+guider(?:\s+camera)?\s+work|不进行维护|作業は行いません', re.I)
_DELAY = re.compile(r'推迟|延后|延迟|改期|延期|改到|postponed|delayed|rescheduled|deferred', re.I)
_NONFAULT = re.compile(r'不是故障|并非故障|不属于故障|没有故障|故障ではない|not\s+(?:a\s+)?fault', re.I)
_RAIN_CONFIRMED = re.compile(r'下雨了|下.{0,1}雨了|已经降雨|已下雨|实测下雨|rain confirmed', re.I)
_RAIN_CONDITION = re.compile(r'(?:如果|如遇|若|假如).{0,8}(?:雨|降雨)|if\s+it\s+rains', re.I)
_SOL = {'do': '1', 're': '2', 'mi': '3', 'fa': '4', 'sol': '5', 'la': '6',
        'si': '7', '高音do': '8', '高音re': '9', '休止': '0'}
_SOL_TOKEN = r'(?:高音\s*(?:do|re)|do|re|mi|fa|sol|la|si|休止)'
_SOL_CLOCK = re.compile(r'(?<![a-z])(' + _SOL_TOKEN + r'(?:\s+' + _SOL_TOKEN + r')?)\s*:\s*(' + _SOL_TOKEN + r'\s+' + _SOL_TOKEN + r')(?![a-z])', re.I)
_REL_FLAT = re.compile(r'第一段|test\s+window\s+(?:no\.?\s*)?1', re.I)
_REL_EVENT = re.compile(r'按钟点|同一时间|时间与上面|(?:by|on) the clock|same local time', re.I)


def _utc(value):
    try:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if not isinstance(value, datetime) or value.tzinfo is None:
            return None
        return value.astimezone(UTC)
    except (ValueError, OverflowError, TypeError):
        return None


def _number(value):
    if value.isdigit():
        return int(value)
    if '十' in value:
        left, right = value.split('十', 1)
        return (_CN.get(left, 1) if left else 1) * 10 + _CN.get(right, 0)
    if all(c in _CN for c in value):
        return int(''.join(str(_CN[c]) for c in value))
    return None


def _normal(text):
    text = unicodedata.normalize('NFKC', text).translate(_TRANSLATE)
    text = re.sub(r'[\u200b-\u200f\ufeff]', '', text)
    # Decorative kaomoji may be inserted inside a date or clock.
    text = re.sub(r'\([^()]*\)', lambda m: m[0] if re.search(r'[A-Za-z0-9\u3400-\u9fff]', m[0]) else '', text)
    text = text.replace('ヽ', '').replace('ノ', '').replace('ﾉ', '')
    text = text.replace('午前', '上午').replace('午後', '下午').replace('午后', '下午')
    def solfege(match):
        parts = []
        for part in match.groups():
            tokens = re.findall(_SOL_TOKEN, part, re.I)
            parts.append(''.join(_SOL[re.sub(r'\s+', '', t).lower()] for t in tokens))
        return ':'.join(parts)
    text = _SOL_CLOCK.sub(solfege, text)
    # A recognized decoded hardware/test phrase, not a guessed cipher key.
    if re.search(r'凯撒|シーザー|加密|英文按约定|钥匙', text) and not re.search(r'guider\s+camera|flat[ -]lamp', text, re.I):
        for shift in range(1, 26):
            def letter(c):
                base = ord('A') if c.isupper() else ord('a')
                return chr((ord(c) - base - shift) % 26 + base) if c.isascii() and c.isalpha() else c
            decoded = ''.join(letter(c) for c in text)
            if re.search(r'guider\s+camera|flat[ -]lamp', decoded, re.I):
                text = decoded
                break
    return text


def _expand_aliases(text, aliases):
    for alias, target in aliases.items():
        # Only an explicit work verb plus a complete alias is actionable.
        text = re.sub(r'(动\s*)' + re.escape(alias) + r'(?=[\s，,。.;；!！]|$)',
                      lambda m: m[1] + target, text)
    return text


def _lines(reason):
    marks = list(re.finditer(r'【([^】]{1,32})】', reason))
    if not marks:
        return [('', t) for t in reason.splitlines() if t.strip()]
    return [(m[1], reason[m.end():marks[i + 1].start() if i + 1 < len(marks) else len(reason)].strip())
            for i, m in enumerate(marks)]


def _clock_matches(text):
    out = []
    for m in _CLOCK.finditer(text):
        if text[max(0, m.start()-1):m.start()] == "同" and m[0] == "一时":
            continue  # 同一时间 is a reference, not a one o'clock timestamp.
        if re.search(r'UTC\s*[+-]\s*$', text[:m.start()], re.I):
            continue
        if m[1] is not None:
            hour, minute = int(m[1]), int(m[2])
        else:
            hour = _number(m[3])
            minute = _number(m[4]) if m[4] else (45 if '三刻' in m[0] else 15 if '一刻' in m[0] else 30 if '半' in m[0] else 0)
        prefix = re.search(r'(凌晨|早上|上午|中午|下午|傍晚|晚上|晚间|夜里)\s*$', text[:m.start()])
        suffix = re.match(r'\s*([ap])\.?m\.?(?![a-z])', text[m.end():], re.I)
        if prefix or suffix:
            pm = prefix[1] in ('中午', '下午', '傍晚', '晚上', '晚间', '夜里') if prefix else None
            if suffix:
                suffix_pm = suffix[1].lower() == 'p'
                if hour is None or not 1 <= hour <= 12 or (pm is not None and pm != suffix_pm):
                    continue
                pm = suffix_pm
            if hour is None or not 0 <= hour < 24:
                continue
            if 1 <= hour <= 12:
                hour = hour % 12 + (12 if pm else 0)
            elif (hour >= 13 and not pm) or (hour == 0 and pm):
                continue  # Inconsistent period and 24-hour clock: abstain.
        if hour is not None and minute is not None and 0 <= hour < 24 and 0 <= minute < 60:
            out.append((m.start(), m.end(), hour, minute))
    return out


def _dates(text, reference):
    out = []
    for match in _DATE.finditer(text):
        month = int(match[1]) if match[1] else _number(match[3])
        day = int(match[2]) if match[2] else _number(match[4])
        options = []
        for year in (reference.year - 1, reference.year, reference.year + 1):
            try:
                options.append(datetime(year, month, day, tzinfo=UTC))
            except (ValueError, TypeError):
                continue
        if options:
            date = min(options, key=lambda value: abs((value - reference).total_seconds()))
            out.append((match.start(), match.end(), date))
    if not out:
        for match in re.finditer(r'(?<![大前后])今天|(?<![大前后])明天|(?<![大前后])后天|(?<![a-z])today(?![a-z])|(?<![a-z])tomorrow(?![a-z])', text, re.I):
            days = {'今天': 0, '明天': 1, '后天': 2, 'today': 0, 'tomorrow': 1}[match[0].lower()]
            date = reference.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=days)
            out.append((match.start(), match.end(), date))
    return out


def _zone(text, offset):
    if re.search(r'(?<![a-z])UTC(?![a-z])', text, re.I):
        explicit = re.search(r'UTC\s*([+-])\s*(\d{1,2})(?::(\d{2}))?', text, re.I)
        if explicit:
            hours = int(explicit[2]) + int(explicit[3] or 0) / 60
            if hours > 14 or int(explicit[3] or 0) >= 60:
                return None, 'invalid'
            hours *= 1 if explicit[1] == '+' else -1
            return hours, 'UTC' + explicit[1] + f'{int(explicit[2]):02}:{int(explicit[3] or 0):02}'
        return 0.0, 'UTC'
    if re.search(r'东京|東京|Tokyo|(?<![a-z])JST(?![a-z])', text, re.I):
        return 9.0, 'UTC+09:00 (Tokyo)'
    if re.search(r'[A-Z]{2,5}\s*(?:时间|時刻)|(?<![a-z])(?:CST|EST|PST|CET|CEST|GMT|BST)(?![a-z])', text, re.I):
        return None, 'unknown or ambiguous zone'
    minutes = round(abs(offset) * 60)
    return offset, f"UTC{'+' if offset >= 0 else '-'}{minutes // 60:02}:{minutes % 60:02} (site)"


def _absolute(text, at, offset):
    parts = re.split(r'[;；]', text)
    dated = [p for p in parts if _dates(p, at) and _clock_matches(p)]
    if len(dated) > 1:
        values, labels = [], []
        for part in dated:
            parsed, label = _absolute(part, at, offset)
            if len(parsed) != 1:
                return [], 'ambiguous compound notice'
            values.extend(parsed); labels.append(label)
        if re.search(r'同一|same\s+(?:event|job)', text, re.I):
            return ([values[0]] if len(set(values)) == 1 else []), ' / '.join(labels)
        # A revision is the only supported meaning of two different zoned times.
        if not _DELAY.search(text) and len(set(labels)) > 1:
            return [], 'ambiguous mixed zones'
        return values, ' / '.join(labels)
    zone, label = _zone(text, offset)
    if zone is None:
        return [], label
    dates = _dates(text, at + timedelta(hours=zone))
    out = []
    for start, end, hour, minute in _clock_matches(text):
        before = [item for item in dates if item[1] <= start]
        date = before[-1][2] if before else dates[0][2] if len(dates) == 1 else None
        if date is not None:
            out.append(date.replace(hour=hour, minute=minute) - timedelta(hours=zone))
    return out, label


def _duration(text):
    """Read an explicit duration; None means unknown, never zero by default."""
    compact = re.sub(r'\s+', '', text)
    compact = compact.replace('一个半小时', '一小时半').replace('个半小时', '小时半')
    hours = re.search(r'(' + _NUM + r')小时(半)?', compact)
    minutes = re.search(r'(' + _NUM + r')分(?:钟)?', compact)
    if hours or minutes:
        return timedelta(minutes=(_number(hours[1]) * 60 + (30 if hours[2] else 0) if hours else 0) + (_number(minutes[1]) if minutes else 0))
    if '半小时' in compact:
        return timedelta(minutes=30)
    words = {'one': 1, 'two': 2, 'three': 3, 'a': 1, 'an': 1}
    if re.search(r'(?:one\s+and\s+a\s+half|an?\s+hour\s+and\s+a\s+half)', text, re.I):
        return timedelta(minutes=90)
    if re.search(r'half\s+an?\s+hour', text, re.I):
        return timedelta(minutes=30)
    matches = list(re.finditer(r'(\d+|one|two|three|an?)\s+(hours?|minutes?)', text, re.I))
    total = 0
    for match in matches:
        count = int(match[1]) if match[1].isdigit() else words[match[1].lower()]
        total += count * (60 if match[2].lower().startswith('hour') else 1)
    if matches:
        return timedelta(minutes=total)
    return None


@dataclass
class ScheduleEvent:
    id: str
    onset_utc: datetime
    publication_utc: datetime
    source_text: str
    source_timezone: str
    source_request_id: str | None = None
    status: str = 'scheduled'
    revisions: list = field(default_factory=list)
    processed_reason: str | None = None
    _updated_utc: datetime | None = None
    _rain_date: str | None = None
    _rain_original: datetime | None = None

    @property
    def due_utc(self):
        return self.onset_utc + timedelta(seconds=GRACE_SECONDS)

    @property
    def text(self):
        return self.source_text

    def ledger(self):
        return {'id': self.id, 'onset_utc': self.onset_utc.isoformat(), 'due_utc': self.due_utc.isoformat(),
                'publication_utc': self.publication_utc.isoformat(), 'source_text': self.source_text,
                'source_request_id': self.source_request_id,
                'source_timezone': self.source_timezone, 'status': self.status,
                'processed_reason': self.processed_reason, 'revisions': list(self.revisions)}


class ScheduleBook:
    """Idempotent schedule ledger. Unknown/invalid offsets disable ingestion.

    ``ingest`` ignores future publications without marking them seen. Records are
    replayed by publication timestamp if delivered out of order; terminal report
    decisions are preserved. ``next_due`` returns future deadlines only; ``due``
    returns already due events. A guard can settle occurred but not-yet-due work.
    """
    def __init__(self, utc_offset_hours, log=None):
        valid = isinstance(utc_offset_hours, (int, float)) and not isinstance(utc_offset_hours, bool)
        self.enabled = valid and math.isfinite(utc_offset_hours) and -14 <= utc_offset_hours <= 14
        self.utc_offset_hours = float(utc_offset_hours) if self.enabled else None
        self.log = log
        self.events = []
        self._aliases = {}
        self._records = {}
        self._processed = {}
        self._processed_after = {}
        self._processed_onsets = {}
        self._flat = {}
        self._rain = {}
        self._last_publication = None
        self.diagnostics = []
        self._source_request_id = None
        self._source_lines = {}

    def __iter__(self):
        return iter(self.events)

    def ingest(self, record, now_utc):
        now = _utc(now_utc)
        if not self.enabled or not isinstance(record, dict) or now is None:
            return
        at = _utc(record.get('issued_at_utc'))
        reason = record.get('reason')
        if at is None or at > now or not isinstance(reason, str) or not reason:
            return
        truncated = len(reason) > MAX_REASON_CHARS
        reason = reason[:MAX_REASON_CHARS]
        if truncated:
            # Do not turn the beginning of a cut-off conditional into a notice.
            reason = reason.rsplit('\n', 1)[0] if '\n' in reason else ''
        key = hashlib.sha256((at.isoformat() + '\n' + reason).encode()).hexdigest()
        if key in self._records or len(self._records) >= MAX_RECORDS:
            return
        request_id = record.get('request_id', record.get('id'))
        request_id = str(request_id)[:160] if request_id is not None else None
        self._records[key] = (at, reason, request_id, truncated)
        if self._last_publication is not None and at < self._last_publication:
            self.events, self._aliases, self._flat, self._rain = [], {}, {}, {}
            self.diagnostics = []
            for publication, text, source_id, was_truncated in sorted(self._records.values(), key=lambda item: item[0]):
                self._source_request_id = source_id
                self._ingest_text(text, publication, was_truncated)
        else:
            self._source_request_id = request_id
            self._ingest_text(reason, at, truncated)
        self._last_publication = max(at, self._last_publication or at)
        for event in self.events:
            if event.id in self._processed:
                event.status = 'processed'
                event.processed_reason = self._processed[event.id]
        self.events.sort(key=lambda event: (event.onset_utc, event.id))

    def _upsert(self, onset, at, raw, zone, action='scheduled', original=None):
        previous, target = self._aliases.get(original or onset), self._aliases.get(onset)
        event = previous or target
        if previous is not None and target is not None and previous is not target:
            # A translated final time may have been published before its revision.
            # Collapse both identities, preserving a report already made for either.
            keep, remove = (target, previous) if target.publication_utc <= previous.publication_utc else (previous, target)
            keep.revisions = (keep.revisions + remove.revisions)[:MAX_REVISIONS]
            if remove.status == 'processed':
                keep.status, keep.processed_reason = remove.status, remove.processed_reason
                self._processed[keep.id] = remove.processed_reason
                self._processed_after[keep.id] = self._processed_after.get(remove.id, remove.publication_utc)
                self._processed_onsets[keep.id] = self._processed_onsets.get(remove.id, remove.onset_utc)
            elif remove.status == 'canceled' and keep.status != 'processed':
                keep.status = 'canceled'
            for alias, value in list(self._aliases.items()):
                if value is remove:
                    self._aliases[alias] = keep
            self.events.remove(remove)
            event = keep
        if event is None:
            if len(self.events) >= MAX_EVENTS:
                return None
            identity = hashlib.sha256(('guider:' + (original or onset).isoformat()).encode()).hexdigest()[:20]
            event = ScheduleEvent(identity, onset, at, raw[:2000], zone,
                                  source_request_id=self._source_request_id)
            self.events.append(event)
        old_onset = event.onset_utc
        self._aliases.setdefault(original or onset, event)
        self._aliases.setdefault(onset, event)
        prior_processed_reason = None
        if (original is not None and action in ('postponed', 'rain_delayed') and
                event.id in self._processed and
                at > self._processed_after[event.id] and
                self._processed_onsets[event.id] <= at < onset):
            # A newly published revision can make an earlier report premature.
            # The publication watermark prevents old out-of-order text rearming it.
            prior_processed_reason = self._processed.pop(event.id)
            self._processed_after.pop(event.id, None)
            self._processed_onsets.pop(event.id, None)
            event.status, event.processed_reason = 'scheduled', None
        # Plain re-statements cannot undo cancellation or move a revised event back.
        if action in ('canceled', 'deferred'):
            if event.status != 'processed':
                event.status = action
        elif original is not None and event.status not in ('canceled', 'processed'):
            event.onset_utc = onset
            event.status = 'scheduled'
        event._updated_utc = at
        revision = {'publication_utc': at.isoformat(), 'source_text': raw[:2000],
                    'source_timezone': zone, 'onset_utc': onset.isoformat(),
                    'source_request_id': self._source_request_id,
                    'source_line': self._source_lines.get(raw),
                    'action': action}
        if original is not None:
            revision['previous_onset_utc'] = old_onset.isoformat()
        if prior_processed_reason is not None:
            revision['prior_processed_reason'] = prior_processed_reason
        if revision not in event.revisions and len(event.revisions) < MAX_REVISIONS:
            event.revisions.append(revision)
        return event

    def _remember_flat(self, text, at):
        if not _FLAT.search(text) or _CAMERA.search(text) or _RUMOR.search(text) or _NEIGHBOR.search(text):
            return
        dates = _dates(text, at + timedelta(hours=self.utc_offset_hours))
        clocks = _clock_matches(text)
        if not dates or len(clocks) < 2:
            return
        date = dates[0][2]
        _, _, h1, m1 = clocks[0]
        _, _, h2, m2 = clocks[1]
        start = date.replace(hour=h1, minute=m1) + timedelta(days=h1 < 12)
        end = date.replace(hour=h2, minute=m2) + timedelta(days=h2 < 12)
        if end <= start:
            end += timedelta(days=1)
        self._flat[date.date().isoformat()] = end - timedelta(hours=self.utc_offset_hours)

    def _ingest_text(self, reason, at, truncated=False):
        lines = [(speaker, raw, _normal(raw)) for speaker, raw in _lines(reason)]
        # Only an explicit definition in this request can resolve an alias.
        definitions = {}
        for _, _, text in lines:
            if _RUMOR.search(text) or _NEIGHBOR.search(text) or _OBSOLETE.search(text) or _UNCERTAIN.search(text):
                continue
            match = re.fullmatch(r'\s*本条暗号[「“]([^」”\d]{1,16})[」”]\s*[=＝]\s*([^。.!！]+)[。.!！]?\s*', text)
            if match:
                definitions.setdefault(match[1], set()).add(match[2].strip())
        aliases = {key: '导星相机' for key, targets in definitions.items() if targets == {'导星相机'}}
        if aliases:
            lines = [(speaker, raw, _expand_aliases(text, aliases)) for speaker, raw, text in lines]
        self._source_lines = {raw: index for index, (_, raw, _) in enumerate(lines, 1)}
        if truncated:
            self._reject(reason, at, 'reason_truncated')
        for _, _, text in lines:
            self._remember_flat(text, at)
        pending = []
        for speaker, raw, text in lines:
            if _RUMOR.search(text) or _NEIGHBOR.search(text) or _OBSOLETE.search(text):
                if _CAMERA.search(text):
                    self._reject(raw, at, 'rumor_or_neighbor')
                continue
            rain_conditional = bool(_RAIN_CONDITION.search(text))
            if _RAIN_CONFIRMED.search(text) and re.search(r'顺延|次日|翌日|next day', text, re.I):
                dates = _dates(text, at + timedelta(hours=self.utc_offset_hours))
                if dates:
                    key = dates[0][2].date().isoformat()
                    self._rain[key] = (at, raw)
                    self._apply_rain(key, at, raw)
                continue
            if not _CAMERA.search(text):
                continue
            # A flat-test disclaimer inside a relative work notice refers to the
            # test, not to the hardware action that follows it.
            if (_NONFAULT.search(text) or _FLAT.search(text)) and not _REL_FLAT.search(text):
                self._reject(raw, at, 'explicit_nonfault')
                continue
            correction = bool(_CORRECTION.search(text))
            if _UNCERTAIN.search(text) and not correction:
                self._reject(raw, at, 'uncertain')
                continue
            if re.search(r'地震|晃动|揺れ', text) and not re.search(r'工程组|guider camera work', text, re.I):
                continue
            if ((_REL_FLAT.search(text) or _REL_EVENT.search(text)) and not rain_conditional
                    and not _DELAY.search(text) and '顺延' not in text):
                pending.append((raw, text))
                continue
            # A bounded outage/closure is not evidence of a persistent fault.
            if (re.search(r'停止|停机|停用|shutdown|downtime', text, re.I)
                    and len(_clock_matches(text)) > 1
                    and not re.search(r'报修|故障報告|fault report|report then', text, re.I)):
                self._reject(raw, at, 'bounded_downtime')
                continue
            times, zone = _absolute(text, at, self.utc_offset_hours)
            relative = re.search(r'本条通知发布后(\d{1,5})分钟', text)
            if relative and 0 < int(relative[1]) <= 31 * 24 * 60 and not times:
                times, zone = [at + timedelta(minutes=int(relative[1]))], 'publication UTC + explicit duration'
            if not times:
                self._reject(raw, at, 'unreadable_time')
                continue
            onset = times[-1] if correction else times[0]
            if correction and len(times) > 1 and times[0] != onset:
                wrong = self._aliases.get(times[0])
                if wrong is not None and wrong.status != 'processed':
                    wrong.status = 'canceled'
            if _CANCEL.search(text) or _NEGATED.search(text):
                self._upsert(onset, at, raw, zone, 'canceled')
                continue
            delay_match = _DELAY.search(text) if not rain_conditional else None
            if delay_match:
                duration = _duration(text[delay_match.end():])
                if len(times) == 2 and times[-1] > times[0]:
                    self._upsert(times[-1], at, raw, zone, 'postponed', original=times[0])
                elif len(times) == 1 and duration is not None and timedelta(0) < duration <= timedelta(days=7):
                    self._upsert(onset + duration, at, raw, zone, 'postponed', original=onset)
                else:
                    self._upsert(onset, at, raw, zone, 'deferred')
                    self._reject(raw, at, 'unreadable_delay')
                continue
            event = self._upsert(onset, at, raw, zone)
            if event and '雨' in text and ('顺延' in text or rain_conditional):
                dates = _dates(text, at + timedelta(hours=self.utc_offset_hours))
                if dates:
                    event._rain_date = dates[0][2].date().isoformat()
                    event._rain_original = onset
                    if event._rain_date in self._rain:
                        rain_at, rain_raw = self._rain[event._rain_date]
                        self._apply_rain(event._rain_date, max(at, rain_at), rain_raw)
        # Relative notices may precede their explicit source in the same request.
        for _ in range(3):
            unresolved = []
            for raw, text in pending:
                if not self._relative(raw, text, at):
                    unresolved.append((raw, text))
            if len(unresolved) == len(pending):
                break
            pending = unresolved
        for raw, _ in unresolved if pending else []:
            self._reject(raw, at, 'unresolved_reference')

    def _reject(self, raw, at, reason):
        if len(self.diagnostics) < MAX_EVENTS:
            self.diagnostics.append({'publication_utc': at.isoformat(),
                                     'source_text': raw[:2000], 'reason': reason,
                                     'source_request_id': self._source_request_id,
                                     'source_line': self._source_lines.get(raw)})

    def _apply_rain(self, date, at, raw):
        for event in list(self.events):
            if event._rain_date == date and event._rain_original is not None:
                self._upsert(event._rain_original + timedelta(days=1), at, raw,
                             event.source_timezone, 'rain_delayed', original=event._rain_original)

    def _relative(self, raw, text, at):
        dates = _dates(text, at + timedelta(hours=self.utc_offset_hours))
        if not dates:
            return False
        _, zone = _zone(text, self.utc_offset_hours)
        if _REL_FLAT.search(text):
            end = self._flat.get(dates[0][2].date().isoformat())
            duration = _duration(text[text.find('第一段'):] if '第一段' in text else text)
            if end is None or duration is None:
                return False
            self._upsert(end + duration, at, raw, zone, 'relative_flat_end')
            return True
        if len(dates) < 2:
            return False
        target, reference = dates[0][2], dates[1][2]
        # Reporting a job settles its action, not the published clock that a later notice can reference.
        candidates = [e for e in self.events if e.status in ('scheduled', 'processed') and
                      (e.onset_utc + timedelta(hours=self.utc_offset_hours)).date() == reference.date()]
        if len(candidates) != 1:
            return False  # Ambiguous clock references never pick an arbitrary event.
        local = candidates[0].onset_utc + timedelta(hours=self.utc_offset_hours)
        change = timedelta(0)
        if re.search(r'按钟点|(?:by|on) the clock', text, re.I):
            match = re.search(r'(早|晚)(' + _NUM + r'|半|\d)', text)
            english = re.search(r'earlier|later', text, re.I)
            if not match and not english:
                return False
            duration = _duration(text[match.start() + 1:] if match else text)
            if duration is None:
                return False
            later = match[1] == '晚' if match else english[0].lower() == 'later'
            change = duration if later else -duration
        clock = local + change
        onset = target.replace(hour=clock.hour, minute=clock.minute) - timedelta(hours=self.utc_offset_hours)
        self._upsert(onset, at, raw, zone, 'relative_event_clock')
        return True

    def due(self, now_utc):
        now = _utc(now_utc)
        if now is None:
            return []
        return [e for e in self.events if e.status == 'scheduled' and e.publication_utc <= now and e.due_utc <= now]

    def next_due(self, now_utc):
        now = _utc(now_utc)
        if now is None:
            return None
        return min((e.due_utc for e in self.events if e.status == 'scheduled' and
                    e.publication_utc <= now and e.due_utc > now), default=None)

    def mark_processed(self, event, reason):
        if event in self.events and event.status == 'scheduled':
            event.status = 'processed'
            event.processed_reason = str(reason)[:240]
            self._processed[event.id] = event.processed_reason
            self._processed_after[event.id] = self._last_publication or event.publication_utc
            self._processed_onsets[event.id] = event.onset_utc

    def settle_through(self, now_utc, reason):
        now = _utc(now_utc)
        if now is None:
            return
        for event in self.events:
            if event.onset_utc <= now:
                self.mark_processed(event, reason)

    def ledger(self):
        return [event.ledger() for event in self.events]


# --- AO_SCHEDULE_LLM: the model confirms a scheduled report before it goes out ------------------------------------
# A held-out wording test (360 unseen lines, 2026-10-07) showed the rules read any line with the camera word, a date and
# a clock time as a job unless a blacklist word hits: unseen corrections, cancellations, delays and decoys (other
# hardware, past notices, nearby telescopes, rumours, tentative plans) still fired (OLD 88 correct / 206 false, NEW
# 112 / 172). The model, at temperature 0, reads those correctly (42-line test: 39/42 right, decoys 8/8). So before a
# scheduled report the model sees the notice and every later relevant line and must confirm that the job is real, ours
# and still on at that time, quoting a supporting fragment that the lines really contain. A refusal settles the event
# without a report; no answer (model off, error, timeout, bad JSON or a quote not found) keeps the rules' decision.

VERIFY_MAX_LINES = 40
VERIFY_LINE_CHARS = 300
_GUIDERISH = re.compile(r'导星|導星|guid|ガイド|ガイダ|autoguid', re.I)
_REVISIONISH = re.compile(r'更正|取消|推迟|推遲|延|改|挪|撤|作废|不做|免了|暂停|中止|恢复|cancel|postpon|delay|moved|resched|scratch|'
                          r'push|called off|withdraw|変更|延期|中止|取りやめ|訂正', re.I)
VERIFY_SYSTEM = (
    "An observatory program read a duty-log NOTICE as announcing work on our telescope's guider camera (导星相机 / guider "
    "camera / ガイドカメラ, or a code word defined for it) and will report a fault at that time. The program already "
    "worked out the time (time zones, relative times, rain rules): do NOT check or recompute times. Answer two questions. "
    "(1) notice_is_job: is the NOTICE itself an announcement of real, firm guider-camera work on OUR telescope? Answer false "
    "only if the notice clearly is about another telescope or another instrument, a rumour or question, an unconfirmed or "
    "tentative plan, an archived or already finished past event, or a flat-lamp / mirror-cover / calibration test with no "
    "guider work. A notice that says a test comes first and the guider work follows is a job. Restating the same job in "
    "another time zone or language is still the job. (2) later_change: does a LATER line (published after the notice) "
    "cancel this job or move it to a different time? Output JSON only: {\"notice_is_job\": true|false, \"later_change\": "
    "true|false, \"evidence\": \"<exact fragment copied from the notice or the later line that decides it>\", \"why\": "
    "\"<at most 15 words>\"}")


def _local(dt, offset):
    return (dt + timedelta(hours=offset)).strftime('%Y-%m-%d %H:%M')


def verification_prompt(book, events, now_utc):
    """(system, user, lines) asking the model about the notices behind `events` (all due now) and the lines published
    after them, or None."""
    now = _utc(now_utc)
    if not book.enabled or now is None or not events:
        return None
    offset = book.utc_offset_hours
    first = min(e.publication_utc for e in events)
    dates = set()
    for e in events:
        local = e.onset_utc + timedelta(hours=offset)
        dates.update({f'{local.month}/{local.day}', f'{local.month}月{local.day}日'})
    sources = sorted({e.source_text[:VERIFY_LINE_CHARS] for e in events})
    later = []
    for at, reason, _, _ in sorted(book._records.values(), key=lambda item: item[0]):
        if at <= first or at > now:
            continue
        for _, raw in _lines(reason):
            text = _normal(raw)
            if _GUIDERISH.search(text) or _REVISIONISH.search(text) or any(d in text for d in dates):
                later.append(f"[{_local(at, offset)}] {raw[:VERIFY_LINE_CHARS]}")
    seen, lines = set(), []
    for line in later[-VERIFY_MAX_LINES:]:
        if line not in seen:
            seen.add(line); lines.append(line)
    times = ', '.join(_local(e.onset_utc, offset) for e in sorted(events, key=lambda e: e.onset_utc))
    user = (f"NOTICE (published {_local(first, offset)} local): " + ' | '.join(sources) + "\n"
            f"(The program's reading: guider work starts {times} site local time.)\n"
            "LATER lines (oldest first, with publication time):\n" + ('\n'.join(lines) if lines else '(none)'))
    return VERIFY_SYSTEM, user, sources + lines


def verification_verdict(answer_text, lines):
    """False (do not report) only when the model says the notice is not a job or a later line changed it, quoting a
    fragment the lines really contain; True when it confirms; None (keep the rules) on anything else."""
    try:
        data = json.loads(answer_text)
    except (TypeError, ValueError):
        match = re.search(r'\{.*\}', answer_text or '', re.S)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except ValueError:
            return None
    if not isinstance(data, dict):
        return None
    job, change = data.get('notice_is_job'), data.get('later_change')
    if not isinstance(job, bool) or not isinstance(change, bool):
        return None
    if job and not change:
        return True
    evidence = _normal(str(data.get('evidence') or '')).strip()
    if len(evidence) < 2:
        return None
    joined = _normal('\n'.join(lines))
    if evidence not in joined and re.sub(r'\s+', '', evidence) not in re.sub(r'\s+', '', joined):
        return None
    return False
