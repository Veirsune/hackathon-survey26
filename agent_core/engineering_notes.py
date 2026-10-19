"""Grounded engineering forecasts followed by bounded throughput diagnostics."""
import hashlib
import json
from statistics import median
from .engineering_protocol import PROMPT, context, normalize, parse
from .llm_client import LLMClient
from .report_budget import all_sky_weather


class EngineeringNotes:
    def __init__(self, log):
        self.client = LLMClient(log=log, call_timeout_seconds=30,
                                total_budget_seconds=240, max_calls=16, budget_profile="engineering")
        self.seen = set()
        self.pending = []
        self.codebook = ''
        self.events = {}
        self.attempt_night = None
        self.reports = 0
        self.paid_attempts = 0

    def collect(self, payload):
        now = parse(payload['now_utc'])
        messages = list(payload.get('new_messages', ())) + list(payload.get('active_requests', ()))
        for msg in messages:
            if msg.get('record_type', 'observation_request') != 'observation_request':
                continue
            note = msg.get('reason')
            if not isinstance(note, str) or not note.strip() or len(note) > 8000:
                continue
            try:
                issued = parse(msg['issued_at_utc'])
                if issued.tzinfo is None or issued > now:
                    continue
            except (ValueError, KeyError, TypeError):
                continue
            digest = hashlib.sha256(note.encode()).hexdigest()
            if digest in self.seen:
                continue
            self.seen.add(digest)
            for line in note.splitlines():
                if any(word in line.lower() for word in ('codebook', 'do=1', 'do = 1', '唱名', '凯撒', '凱撒')):
                    self.codebook = (self.codebook + '\n' + line)[-3000:]
            if not any(word in note.lower() for word in
                       ('工程', '导星', '導星', '效率', '仪器', '儀器', 'instrument', 'engineering', 'guide camera', 'efficiency', 'maintenance')):
                continue
            self.pending.append(dict(note=note, issued_at_utc=msg['issued_at_utc'], attempts=0))
        self.pending.sort(key=lambda r: parse(r['issued_at_utc']))
        self.pending = self.pending[-16:]

    def review(self, planner, payload):
        client = self.client
        night = planner.night_index_seen
        client.begin_night(night)
        if (not self.pending or night is None or self.attempt_night == night
                or not client.retry_available or planner._wall_left() <= 100
                or planner._cpu_left() <= 10):
            return
        row = self.pending[0]
        try:
            ctx = context(row['note'], row['issued_at_utc'], payload['now_utc'],
                          planner.state.utc_offset_hours, self.codebook)
        except (ValueError, TypeError):
            self.pending.pop(0)
            return
        self.attempt_night = night
        row['attempts'] += 1
        answer = client.ask_json(PROMPT + '\nFor a corrected event time, include a withdrawn record for the superseded time if the note explicitly identifies it.',
                                 ctx, planner._wall_left(), stage='engineering_notes')
        try:
            forecasts = normalize(answer, ctx)
        except (ValueError, TypeError):
            if row['attempts'] >= 2:
                self.pending.pop(0)
            planner.log('engineering_note_advice: ' + json.dumps(dict(accepted=False, status=client.last_status)))
            return
        self.pending.pop(0)
        for forecast in forecasts:
            key = forecast['onset_utc']
            old = self.events.get(key)
            if old and parse(old['source_issued_local']) > parse(forecast['source_issued_local']):
                continue
            forecast.update(attempted=bool(old and old['attempted']), reference=None,
                            accepted_at_utc=payload['now_utc'])
            self.events[key] = forecast
        planner.log('engineering_note_advice: ' + json.dumps(dict(accepted=True, forecasts=forecasts), ensure_ascii=False))

    def report(self, planner, hours, payload):
        state = planner.state
        if (getattr(planner, '_await_report_result', False) or self.reports >= 8
                or planner.consecutive_reports >= state.max_consecutive_reports):
            return None
        for key, event in sorted(self.events.items()):
            onset = (parse(key) - state.survey_start).total_seconds() / 3600
            if event['status'] != 'asserted' or event['attempted'] or hours > onset + 48:
                continue
            # Any report already made after this forecast's onset consumes its opportunity.
            if planner.last_report_hours >= onset:
                event['attempted'] = True
                continue
            rows = getattr(state, '_weather_clear_diagnostic_exposures', ())
            before = [r for t, _, r in rows if onset - 72 <= t < onset]
            if len(before) >= 3:
                event['reference'] = median(before)
            reference = event['reference']
            # Use only subsequent complete exposures, with separated endpoints.
            after = [(t, r) for t, _, r in rows if onset + 1 <= t <= hours]
            if hours < onset or reference is None or reference <= 0 or len(after) < 2:
                continue
            recent = after[-3:]
            if hours - recent[-1][0] > 2 or recent[-1][0] - recent[0][0] < .25:
                continue
            ratio = max(r for _, r in recent) / reference
            if ratio >= .75 or hours - planner.last_report_hours < 24:
                continue
            if all_sky_weather(state.notices) or hours - getattr(state, '_earthquake_seen_hours', float('-inf')) < 7 * 24:
                continue
            paid = getattr(planner, '_false_since_correct', 0) >= state.false_report_free_allowance
            if paid and self.paid_attempts >= 2:
                continue
            event['attempted'] = True
            self.reports += 1
            if paid:
                self.paid_attempts += 1
                planner._paid_diagnostic_attempts = getattr(planner, '_paid_diagnostic_attempts', 0) + 1
            planner.reports += 1
            planner.last_report_hours = hours
            planner._await_report_result = True
            planner._pending_report_ratio = ratio
            planner.suspicion_hours = []
            planner.log('engineering_diagnostic: ' + json.dumps(dict(onset_utc=key, now_utc=payload['now_utc'], ratio=ratio, paid=paid)))
            return dict(action='report', reason='Delivered engineering forecast followed by sustained measured throughput loss', decision_source='llm-engineering-evidence')
        return None
