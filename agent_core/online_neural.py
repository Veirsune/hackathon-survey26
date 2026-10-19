"""Small online nonlinear residual model; one batch update per exposure.

Fixed initialization, bounded inputs/Huber gradients and cold-start shrinkage.
Only delivered score residuals are labels. This is not reinforcement learning.
"""
import math
import numpy as np


class NeuralModel:
    def __init__(self):
        rng=np.random.default_rng(2026)
        self.w1=rng.normal(0,1/math.sqrt(10),(10,12))
        self.b1=np.zeros(12)
        self.w2=np.zeros(12)
        self.b2=0.
        self.exposures=0
        self.total_updates=0
        self.changes=0
        self.last_residual=0.
        self.squared_error=0.
        self.baseline_squared_error=0.
        self.pending=None

    def predict(self,x):
        hidden=np.tanh(np.clip(x,-3,3)@self.w1+self.b1)
        raw=float(hidden@self.w2+self.b2)
        # A sample-count gate, not calibrated epistemic uncertainty.
        raw*=self.exposures/(self.exposures+32.)
        return max(-math.log(4),min(math.log(4),raw))

    def update(self,rows):
        if not rows:return
        x=np.clip(np.stack([r[0] for r in rows]),-3,3)
        y=np.array([r[1] for r in rows])
        hidden=np.tanh(x@self.w1+self.b1)
        raw=hidden@self.w2+self.b2
        predicted=np.clip(raw*self.exposures/(self.exposures+32.),-math.log(4),math.log(4))
        self.squared_error+=float(np.mean((y-predicted)**2))
        self.baseline_squared_error+=float(np.mean(y*y))
        # Correlated fibres have total weight one, regardless of fibre count.
        error=np.clip(raw-y,-1,1)/len(rows)
        back=error[:,None]*self.w2[None,:]*(1-hidden*hidden)
        dw1=x.T@back+1e-4*self.w1
        db1=back.sum(axis=0)
        dw2=hidden.T@error+1e-4*self.w2
        db2=float(error.sum())
        norm=math.sqrt(float(np.sum(dw1*dw1)+np.sum(db1*db1)+np.sum(dw2*dw2)+db2*db2))
        step=.02/max(1.,norm)
        self.w1-=step*dw1
        self.b1-=step*db1
        self.w2-=step*dw2
        self.b2-=step*db2
        self.last_residual=float(np.median(y))
        self.exposures+=1
        self.total_updates+=1
