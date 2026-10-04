"""Calendar-accrued CPU credit with actual platform expenditure feedback."""
from bisect import bisect_right
import math

class CalendarGovernor:
    def __init__(self, nights, minimum_exposure):
        self.starts=[a for a,b in nights];self.ends=[b for a,b in nights]
        self.suffix=[0.]*(len(nights)+1)
        for i in range(len(nights)-1,-1,-1):
            self.suffix[i]=self.suffix[i+1]+max(0.,(nights[i][1]-nights[i][0]).total_seconds())
        self.minimum=max(1.,minimum_exposure);self.costs=[None]*3;self.last=[None]*3
        self.overhead=None;self.overhead_count=0;self.advance=None;self.search_count=0
        self.last_forecast=None
        self.review_cost=None;self.last_review_cost=None
        self.initial_remaining=None;self.initial_calendar_seconds=None

    def record(self, cpu, tier, searched, advance=0.):
        if not math.isfinite(cpu) or cpu<0:return
        if searched:
            old=self.costs[tier];self.costs[tier]=cpu if old is None else .8*old+.2*cpu
            self.last[tier]=cpu;self.search_count+=1
            if advance>0 and math.isfinite(advance):
                self.advance=advance if self.advance is None else .8*self.advance+.2*advance
        else:
            self.overhead=cpu if self.overhead is None else .8*self.overhead+.2*cpu
            self.overhead_count+=1

    def record_review(self, cpu):
        if not math.isfinite(cpu) or cpu<0:return
        self.review_cost=cpu if self.review_cost is None else .8*self.review_cost+.2*cpu
        self.last_review_cost=cpu

    def calendar(self, now):
        done=bisect_right(self.ends,now);n=len(self.ends)-done
        seconds=self.suffix[done]
        if n and now>self.starts[done]:seconds-=min((now-self.starts[done]).total_seconds(),(self.ends[done]-self.starts[done]).total_seconds())
        return max(0.,seconds),n,done

    def choose(self, now, remaining, current, reviews_left=0):
        if not self.ends or not math.isfinite(remaining):
            self.last_forecast={'reason':'legacy_unknown_forecast'}
            return 0 if remaining>180. else 2
        costs=[None if a is None else max(a,b) for a,b in zip(self.costs,self.last)]
        finish_reserve=max(5.,4*max((v for v in costs if v is not None),default=0.))
        review_reserve=max(0,reviews_left)*max(self.review_cost or 0.,self.last_review_cost or 0.)
        reserve=finish_reserve+review_reserve
        seconds,n,done=self.calendar(now)
        if self.initial_remaining is None:
            self.initial_remaining=max(0.,remaining)
            self.initial_calendar_seconds=max(1.,seconds)
        if remaining<=reserve:
            self.last_forecast={'reason':'finish_reserve','reserve':reserve};return 2
        if any(v is None for v in costs):
            if remaining<=reserve+4*max(1.,max((v for v in costs if v is not None),default=0.)):
                self.last_forecast={'reason':'cold_budget_reserve','reserve':reserve};return 2
            tier=next(i for i,v in enumerate(costs) if v is None)
            self.last_forecast={'reason':'cold_calibration','tier':tier,'reserve':reserve};return tier
        # Credit is released by public observing time, with a 2% startup
        # allowance. Actual remaining CPU already includes ALL spent work:
        # reviews, waits, feedback, search and calibration, at platform speed.
        fraction=min(1.,max(0.,1.-seconds/self.initial_calendar_seconds))
        spent=max(0.,self.initial_remaining-remaining)
        allowance=max(0.,self.initial_remaining-reserve)*(.02+.98*fraction)
        credit=allowance-spent
        feasible=[i for i,c in enumerate(costs) if c is not None and c<=credit]
        tier=min(feasible,default=2)
        self.last_forecast={'reason':'calendar_credit','remaining_seconds':seconds,
            'calendar_fraction':fraction,'actual_cpu_spent':spent,
            'accrued_cpu':allowance,'credit_cpu':credit,'costs':costs,
            'reserve':reserve,'review_reserve':review_reserve}
        return tier
