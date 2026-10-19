"""Delivered work schedules drive reports; unexplained losses keep existing diagnostics.

The MIT Argelander parser supplies event provenance, timestamps and revisions.
This module owns action arbitration and feedback, not text interpretation.
"""
from datetime import timedelta
import json
import math
from .geometry import parse_utc
from .vendor_notes_schedule import ScheduleBook


class ScheduledOperations:
    def __init__(self, state, log, reporting):
        self.book = ScheduleBook(state.utc_offset_hours)
        self.log = log
        self.reporting = reporting
        self.pending = False
        self.sent = self.correct = self.false = 0

    def collect(self, planner, payload):
        now = parse_utc(payload['now_utc'])
        result = payload.get('last_result') or {}
        # Each decision payload is consumed once by the planner. Mark events as
        # handled only when this repair or their own scheduled attempt handled them.
        if result.get('action') == 'report' and isinstance(result.get('correct'), bool):
            if self.pending:
                self.correct += int(result['correct'])
                self.false += int(not result['correct'])
                self.pending = False
            if result['correct']:
                at = planner.state.survey_start + timedelta(hours=planner.last_report_hours)
                self.book.settle_through(at, 'correct shared repair')
        for record in list(payload.get('new_messages', ())) + list(payload.get('active_requests', ())):
            if record.get('record_type', 'observation_request') == 'observation_request':
                self.book.ingest(record, now)

    def eligible(self, planner):
        used = getattr(planner, '_false_since_correct', 0)
        if used < planner.state.false_report_free_allowance:
            return True
        # When guesses cost points, require positive lower-confidence expected
        # immediate reward. No invented probability from a language model.
        if self.correct == 0:
            return False
        a, b = self.correct + 1, self.false + 1
        p = a / (a + b) - math.sqrt(a*b / ((a+b)**2 * (a+b+1)))
        config = self.reporting
        return p * config['correct_reward'] + (1-p) * config['false_penalty'] > 0

    def report(self, planner, hours, payload):
        if getattr(planner, '_await_report_result', False) or not self.eligible(planner):
            return None
        now = parse_utc(payload['now_utc'])
        due = self.book.due(now)
        if not due:
            return None
        if planner.consecutive_reports >= planner.state.max_consecutive_reports:
            return dict(action='wait', duration_seconds=planner.state.min_exposure,
                        reason='Separate scheduled reports by elapsed observing time')
        for event in due:
            self.book.mark_processed(event, 'scheduled report attempted')
        self.sent += 1
        self.pending = True
        planner.reports += 1
        planner.last_report_hours = hours
        planner._await_report_result = True
        planner._pending_report_ratio = 1.0
        planner.suspicion_hours = []
        self.log('scheduled_operation: ' + json.dumps(dict(now_utc=payload['now_utc'],
                 events=[e.id for e in due], sent=self.sent)))
        return dict(action='report', reason='Delivered instrument-work schedule is due',
                    decision_source='scheduled-operation')

    def next_due(self, planner, now):
        return self.book.next_due(now) if self.eligible(planner) else None

    def summary(self):
        return dict(sent=self.sent, correct=self.correct, false=self.false,
                    ledger=self.book.ledger())
