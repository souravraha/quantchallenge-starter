"""
Quant Challenge 2025

Algorithmic strategy template
"""

from enum import Enum
from typing import Optional
import math, time
from collections import deque

class Side(Enum):
    BUY = 0
    SELL = 1

class Ticker(Enum):
    # TEAM_A (home team)
    TEAM_A = 0

def place_market_order(side: Side, ticker: Ticker, quantity: float) -> None:
    """Place a market order.
    
    Parameters
    ----------
    side
        Side of order to place
    ticker
        Ticker of order to place
    quantity
        Quantity of order to place
    """
    return

def place_limit_order(side: Side, ticker: Ticker, quantity: float, price: float, ioc: bool = False) -> int:
    """Place a limit order.
    
    Parameters
    ----------
    side
        Side of order to place
    ticker
        Ticker of order to place
    quantity
        Quantity of order to place
    price
        Price of order to place
    ioc
        Immediate or cancel flag (FOK)

    Returns
    -------
    order_id
        Order ID of order placed
    """
    return 0

def cancel_order(ticker: Ticker, order_id: int) -> bool:
    """Cancel an order.
    
    Parameters
    ----------
    ticker
        Ticker of order to cancel
    order_id
        Order ID of order to cancel

    Returns
    -------
    success
        True if order was cancelled, False otherwise
    """
    return 0

T_FORCE=2.0; T_FLAT_START=45.0; MAX_SPREAD=0.8; MIN_DEPTH=20.0
def win_prob(sd,tsec):
    t=max(tsec,0.0)/60.0; rt=math.sqrt(max(t,1e-6))
    z=0.0+0.065*sd+0.22*rt-0.015*sd*rt
    p=1/(1+math.exp(-z)); return min(max(p,1e-4),1-1e-4)

def edge(tsec): return 0.006+0.014/(1.0+max(tsec,0.0)/60.0)

class Strategy:
    """Template for a strategy."""

    def reset_state(self) -> None:
        """Reset the state of the strategy to the start of game position.
        
        Since the sandbox execution can start mid-game, we recommend creating a
        function which can be called from __init__ and on_game_event_update (END_GAME).

        Note: In production execution, the game will start from the beginning
        and will not be replayed.
        """
        self.bid=self.ask=float("nan"); self.bsz=self.asz=0.0
        self.time_seconds=2880.0; self.hs=self.as_=0; self.pos=0.0; self.avg=0.0
        self.mid_prev=50.0; self.fv_fast=self.fv_slow=50.0; self.vol=0.0
        self.resting={}
        self.snap=0; self.last_snap=time.time()

    def __init__(self) -> None:
        """Your initialization code goes here."""
        self.reset_state()

        # ShockFadeSniper
        self.dM_prev=0.0; self.fv_prev=self.fv_fast

        # # NarrativeTrap, LiquidityTrap
        # self.hold_ms=80

        # # FalseMomentumLure
        # self.skew=1.5

        # HFT
        self.last_ioc=0.0; self.alpha_vol=0.2

    def on_trade_update(
        self, ticker: Ticker, side: Side, quantity: float, price: float
    ) -> None:
        """Called whenever two orders match. Could be one of your orders, or two other people's orders.
        Parameters
        ----------
        ticker
            Ticker of orders that were matched
        side:
            Side of orders that were matched
        quantity
            Volume traded
        price
            Price that trade was executed at
        """
        print(f"Python Trade update: {ticker} {side} {quantity} shares @ {price}")

    def on_orderbook_update(
        self, ticker: Ticker, side: Side, quantity: float, price: float
    ) -> None:
        """Called whenever the orderbook changes. This could be because of a trade, or because of a new order, or both.
        Parameters
        ----------
        ticker
            Ticker that has an orderbook update
        side
            Which orderbook was updated
        price
            Price of orderbook that has an update
        quantity
            Volume placed into orderbook
        """
        if ticker!=Ticker.TEAM_A: return
        if side==Side.BUY:
            if quantity>0 and (math.isnan(self.bid) or price>self.bid): self.bid,self.bsz=price, quantity
        else:
            if quantity>0 and (math.isnan(self.ask) or price<self.ask): self.ask,self.asz=price, quantity
        self._tick()

    def on_account_update(
        self,
        ticker: Ticker,
        side: Side,
        price: float,
        quantity: float,
        capital_remaining: float,
    ) -> None:
        """Called whenever one of your orders is filled.
        Parameters
        ----------
        ticker
            Ticker of order that was fulfilled
        side
            Side of order that was fulfilled
        price
            Price that order was fulfilled at
        quantity
            Volume of order that was fulfilled
        capital_remaining
            Amount of capital after fulfilling order
        """
        if ticker!=Ticker.TEAM_A: return
        s=quantity if side==Side.BUY else -quantity; new=self.pos+s
        if self.pos==0 or (self.pos>0 and s>0) or (self.pos<0 and s<0):
            self.avg=(self.avg*abs(self.pos)+price*abs(s))/max(abs(new),1e-9)
        else:
            if abs(new)<1e-12: self.avg=0.0
            else: self.avg=price
        self.pos=new

    def on_game_event_update(self,
                           event_type: str,
                           home_away: str,
                           home_score: int,
                           away_score: int,
                           player_name: Optional[str],
                           substituted_player_name: Optional[str],
                           shot_type: Optional[str],
                           assist_player: Optional[str],
                           rebound_type: Optional[str],
                           coordinate_x: Optional[float],
                           coordinate_y: Optional[float],
                           time_seconds: Optional[float]
        ) -> None:
        """Called whenever a basketball game event occurs.
        Parameters
        ----------
        event_type
            Type of event that occurred
        home_score
            Home team score after event
        away_score
            Away team score after event
        player_name (Optional)
            Player involved in event
        substituted_player_name (Optional)
            Player being substituted out
        shot_type (Optional)
            Type of shot
        assist_player (Optional)
            Player who made the assist
        rebound_type (Optional)
            Type of rebound
        coordinate_x (Optional)
            X coordinate of shot location in feet
        coordinate_y (Optional)
            Y coordinate of shot location in feet
        time_seconds (Optional)
            Game time remaining in seconds
        """

        print(f"{event_type} {home_score} - {away_score}")
        if home_score is not None: self.hs=int(home_score)
        if away_score is not None: self.as_=int(away_score)
        if time_seconds is not None: self.time_seconds=float(time_seconds)
        self._tick()

        if event_type == "END_GAME":
            # IMPORTANT: Highly recommended to call reset_state() when the
            # game ends. See reset_state() for more details.
            self._force_flat()
            self.reset_state()
            return

    def on_orderbook_snapshot(self, ticker: Ticker, bids: list, asks: list) -> None:
        """Called periodically with a complete snapshot of the orderbook.

        This provides the full current state of all bids and asks, useful for 
        verification and algorithms that need the complete market picture.

        Parameters
        ----------
        ticker
            Ticker of the orderbook snapshot (Ticker.TEAM_A)
        bids
            List of (price, quantity) tuples for all current bids, sorted by price descending
        asks  
            List of (price, quantity) tuples for all current asks, sorted by price ascending
        """
        # Reset the state of local books
        if ticker!=Ticker.TEAM_A: return
        self.bid, self.bsz = (bids[0] if bids else (float("nan"),0.0))
        self.ask, self.asz = (asks[0] if asks else (float("nan"),0.0))
        self.snap+=1; self.last_snap=time.time(); self._tick()

    def _tick(self):
        if self.time_seconds<=T_FORCE: self._force_flat(); return
        if not self._has_top(): return
        mid=self._mid(); self.vol=(1-self.alpha_vol)*self.vol+self.alpha_vol*abs(mid-self.mid_prev); self.mid_prev=mid
        fv=self._fv(); self._act(fv, mid)
    
    def _force_flat(self):
        if not self._has_top():
            if self.pos>0: place_market_order(Side.SELL,Ticker.TEAM_A,abs(self.pos))
            elif self.pos<0: place_market_order(Side.BUY,Ticker.TEAM_A,abs(self.pos))
        else:
            if self.pos>0: place_limit_order(Side.SELL,Ticker.TEAM_A,abs(self.pos),self.bid,ioc=True)
            elif self.pos<0: place_limit_order(Side.BUY,Ticker.TEAM_A,abs(self.pos),self.ask,ioc=True)

        self.pos=0.0; self._cancel_all()
    
    def _has_top(self): return (self.bsz>0 and self.asz>0 and not math.isnan(self.bid) and not math.isnan(self.ask))

    def _mid(self): return (self.bid+self.ask)/2 if self._has_top() else self.mid_prev

    def _fv(self):
        p=win_prob(self.hs-self.as_, self.time_seconds); fv=100.0*p
        self.fv_fast=0.5*fv+0.5*self.fv_fast; self.fv_slow=0.05*fv+0.95*self.fv_slow
        return self.fv_fast

    def _act(self,fv,mid):
        # FundamentalArcarb
        if not self._liq_ok(): return
        e=edge(self.time_seconds)*0.8 
        e_adapt=e + 1.2*self.vol
        # long_room, short_room = self._room(mid, limit_early=8000.0, limit_late=12000.0)
        # if (fv - self.ask) >= e and long_room>0:
        #     px=min(self.ask, fv-0.5*e); place_limit_order(Side.BUY, Ticker.TEAM_A, min(self.asz, max(1.0,long_room*0.2)), px, ioc=True)
        # elif (self.bid - fv) >= e and short_room>0:
        #     px=max(self.bid, fv+0.5*e); place_limit_order(Side.SELL, Ticker.TEAM_A, min(self.bsz, max(1.0,short_room*0.2)), px, ioc=True)
        # if self.time_seconds<=T_FLAT_START:
        #     if self.pos>0 and self.bsz>0: place_limit_order(Side.SELL,Ticker.TEAM_A, min(self.pos,self.bsz), self.bid, ioc=False)
        #     if self.pos>0 and self.asz>0: place_limit_order(Side.BUY,Ticker.TEAM_A, min(-self.pos,self.asz), self.ask, ioc=False)

        # ShockFadeSniper
        dM=mid-self.mid_prev; dFV=fv-self.fv_prev; self.fv_prev=fv
        z=dM-dFV
        max_pos=min(100.0, (self.time_seconds/T_FLAT_START)*100.0*max(0.5, 1.0/(1.0+self.vol))) 
        if abs(self.pos)>max_pos: self._force_flat(); return

        # e=edge(self.time_seconds)
        # if not self._liq_ok(): return
        if time.time()-self.last_ioc>=0.05:
            if z>e_adapt and self.asz>0:
                px=min(self.ask, fv-0.3*e); place_limit_order(Side.BUY,Ticker.TEAM_A, min(self.asz,10.0), px, ioc=True)
                self.last_ioc=time.time()
            elif -z>e_adapt and self.bsz>0:
                px=max(self.bid, fv+0.3*e); place_limit_order(Side.SELL,Ticker.TEAM_A, min(self.bsz,10.0), px, ioc=True)
                self.last_ioc=time.time()

        # EndgameSponge
        # if not self._liq_ok(): return
        if self.time_seconds<=T_FLAT_START:
            if self.pos>0 and self.bsz>0:
                oid=place_limit_order(Side.SELL,Ticker.TEAM_A,min(self.pos,self.bsz), self.bid, ioc=False); self.resting[oid]=time.time()
            elif self.pos<0 and self.asz>0:
                oid=place_limit_order(Side.BUY,Ticker.TEAM_A,min(-self.pos,self.asz), self.ask, ioc=False); self.resting[oid]=time.time()
        for oid,ts in list(self.resting.items()):
            if (time.time()-ts)*1000>=80:
                cancel_order(Ticker.TEAM_A, oid); self.resting.pop(oid, None)

        # # NarrativeTrap
        # if not self._liq_ok(): self._cancel_all(); return
        # e=edge(self.time_seconds)
        # bias_up=(self.hs-self.as_)>0
        # if bias_up and self.asz>0:
        #     oid=place_limit_order(Side.BUY, Ticker.TEAM_A, min(3.0,self.asz), min(self.ask, fv-0.3*e), ioc=False); self.resting[oid]=time.time()
        # if (not bias_up) and self.bsz>0:
        #     oid=place_limit_order(Side.SELL, Ticker.TEAM_A, min(3.0,self.bsz), min(self.bid, fv+0.3*e), ioc=False); self.resting[oid]=time.time()
        # if (mid-fv)>=e and self.bsz>0:
        #     place_limit_order(Side.SELL,Ticker.TEAM_A,min(5.0,self.bsz), max(self.bid, fv+0.5*e), ioc=True)
        # if (fv-mid)>=e and self.asz>0:
        #     place_limit_order(Side.BUY,Ticker.TEAM_A,min(5.0,self.asz), max(self.ask, fv-0.5*e), ioc=True)
        # for oid,ts in list(self.resting.items()):
        #     if (time.time()-ts)*1000>=self.hold_ms: cancel_order(Ticker.TEAM_A, oid); self.resting.pop(oid,None)

        # # FalseMomentumLure
        # if not self._liq_ok(): self._cancel_all(); return
        # e=edge(self.time_seconds)
        # want_down=(mid>fv)
        # if not want_down and self.asz>0:
        #     oid=place_limit_order(Side.BUY, Ticker.TEAM_A, min(10.0,self.asz*self.skew), min(self.ask, fv-0.5*e), ioc=False); self.resting[oid]=time.time()
        # elif want_down and self.bsz>0:
        #     oid=place_limit_order(Side.SELL, Ticker.TEAM_A, min(10.0,self.bsz*self.skew), min(self.bid, fv+0.5*e), ioc=False); self.resting[oid]=time.time()
        # if (mid-fv)>=e and self.bsz>0:
        #     place_limit_order(Side.SELL,Ticker.TEAM_A,min(10.0,self.bsz), max(self.bid, fv+0.5*e), ioc=True)
        # if (fv-mid)>=e and self.asz>0:
        #     place_limit_order(Side.BUY,Ticker.TEAM_A,min(10.0,self.asz), max(self.ask, fv-0.5*e), ioc=True)
        # self._cancel_all()

        # # LiquidityTrap
        # if not self._liq_ok(): self._cancel_all(); return
        # if self.asz>0:
        #     oid=place_limit_order(Side.BUY, Ticker.TEAM_A, min(self.asz,5.0), min(self.ask, fv-0.5*edge(self.time_seconds)), ioc=False)
        #     self.resting[oid]=time.time()
        # if self.bsz>0:
        #     oid=place_limit_order(Side.SELL, Ticker.TEAM_A, min(self.bsz,5.0), min(self.bid, fv+0.5*edge(self.time_seconds)), ioc=False)
        #     self.resting[oid]=time.time()
        # for oid,ts in list(self.resting.items()):
        #     if (time.time()-ts)*1000>=self.hold_ms: cancel_order(Ticker.TEAM_A, oid); self.resting.pop(oid,None)

    def _cancel_all(self):
        for oid in list(self.resting): cancel_order(Ticker.TEAM_A, oid); self.resting.pop(oid, None)

    def _liq_ok(self):
        return self._has_top() and (self.ask-self.bid)<=MAX_SPREAD and (self.bsz+self.asz)>=MIN_DEPTH
    
    def _room(self,mid,limit_early=15000.0,limit_late=30000.0):
        lim = limit_early if self.time_seconds>T_FLAT_START else limit_late*(self.time_seconds/max(T_FLAT_START,1e-9))
        cap=max(1.0, lim/max(mid,1.0)); return max(0.0, cap-max(self.pos,0.0)), max(0.0, cap-max(-self.pos,0.0))
