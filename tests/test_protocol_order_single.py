import os
import time
import unittest
import xml.etree.ElementTree as ET
from math import nan

import pytest

from asyncfix import FTag, FMsg
from asyncfix.protocol.common import FExecType, FOrdSide, FOrdStatus, FOrdType
from asyncfix.protocol.fix_tester import FIXTester
from asyncfix.protocol.order_single import FIXNewOrderSingle
from asyncfix.protocol.schema import FIXSchema

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
fix44_schema = ET.parse(os.path.join(TEST_DIR, "FIX44.xml"))
FIX_SCHEMA = FIXSchema(fix44_schema)


def test_init_order_single_default_short():
    ord_dict = {}
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.SELL, price=100.0, qty=20
    )
    ord_dict[1] = o
    #  cdef FIXNewOrderSingle o2
    for k, v in ord_dict.items():
        o2 = v
        o2.is_finished()
        # v.is_finished() # AttributeError: 'uberhf.orders.fix_orders.FIXNewOrderSingle' object has no attribute 'is_finished'

    assert isinstance(o, FIXNewOrderSingle)
    assert o.status == FOrdStatus.CREATED
    assert o.ord_type == FOrdType.LIMIT
    assert o.price == 100
    assert o.qty == 20
    assert o.leaves_qty == 0
    assert o.cum_qty == 0
    assert o.clord_id == "clordTest"
    assert o.orig_clord_id is None
    assert o.side == FOrdSide.SELL
    assert o.target_price == 100
    assert o.ord_type == FOrdType.LIMIT

    m = o.new_req()

    # Account
    assert m[FTag.Account] == "000000"

    # Tag 11: ClOrdID
    assert m[FTag.ClOrdID] == 'clordTest'

    # Tag 38: Order Qty
    assert m[FTag.OrderQty] == "20"

    # Tag 40: Order Type
    assert m[FTag.OrdType] == "2"  # Limit order

    # Tag 44: Order Price
    assert m[FTag.Price] == "100.0"

    # Tag 54: Side
    assert m[54] == "2"  # sell

    #  Tag 55: Symbol set to v2 symbol
    assert m[FTag.Symbol] == "US.F.TICKER"

    # Overall message is valid!
    assert FIX_SCHEMA.validate(m)


def test_init_order_single_long():
    o = FIXNewOrderSingle(
        "clordTest",
        "US.F.TICKER",
        side=FOrdSide.BUY,
        price=200.0,
        qty=20,
        target_price=220,
        ord_type=FOrdType.MARKET,
    )
    assert isinstance(o, FIXNewOrderSingle)
    assert o.status == FOrdStatus.CREATED
    assert o.price == 200
    assert o.qty == 20
    assert o.leaves_qty == 0
    assert o.cum_qty == 0
    assert o.clord_id == "clordTest"
    assert o.orig_clord_id is None
    assert o.side == FOrdSide.BUY
    assert o.target_price == 220
    assert o.ord_type == FOrdType.MARKET

    m = o.new_req()

    # Account
    assert m[1] == "000000"

    # Tag 11: ClOrdID
    assert m[11] == "clordTest"

    # Tag 38: Order Qty
    assert m[38] == "20"

    # Tag 40: Order Type
    assert m[40] == "1"

    # Tag 44: Order Price
    assert m[44] == "200.0"

    # Tag 54: Side
    assert m[54] == "1"  # buy

    #  Tag 55: Symbol set to v2 symbol
    assert m[55] == 'US.F.TICKER'

    # Overall message is valid!
    assert FIX_SCHEMA.validate(m)


def test_simple_execution_report_state_created__2__pending_new():
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=20
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.PENDING_NEW, f"o.status={chr(o.status)}"


def test_simple_execution_report_state_created__2__rejected():
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=20
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(o, o.clord_id, FExecType.REJECTED, FOrdStatus.REJECTED)
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.REJECTED, f"o.status={chr(o.status)}"


def test_state_transition__created__execution_report():
    # fmt: off
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.CREATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.NEW) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.PARTIALLY_FILLED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.FILLED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.DONE_FOR_DAY) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.CANCELED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.PENDING_CANCEL) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.STOPPED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.REJECTED) == FOrdStatus.REJECTED
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.SUSPENDED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.PENDING_NEW) == FOrdStatus.PENDING_NEW
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.CALCULATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.EXPIRED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.ACCEPTED_FOR_BIDDING) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.CREATED, '8', FExecType.TRADE, FOrdStatus.PENDING_REPLACE) == -23
    # fmt: on


def test_state_transition__pendingnew__execution_report():
    # fmt: off
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.CREATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.NEW) == FOrdStatus.NEW
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.PARTIALLY_FILLED) == FOrdStatus.PARTIALLY_FILLED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.FILLED) == FOrdStatus.FILLED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.DONE_FOR_DAY) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.CANCELED) == FOrdStatus.CANCELED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.PENDING_CANCEL) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.STOPPED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.REJECTED) == FOrdStatus.REJECTED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.SUSPENDED) == FOrdStatus.SUSPENDED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.PENDING_NEW) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.CALCULATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.EXPIRED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.ACCEPTED_FOR_BIDDING) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_NEW, '8', FExecType.TRADE, FOrdStatus.PENDING_REPLACE) == -23
    # fmt: on


def test_state_transition__new__execution_report():
    # fmt: off
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.CREATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.PARTIALLY_FILLED) == FOrdStatus.PARTIALLY_FILLED
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.FILLED) == FOrdStatus.FILLED
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.DONE_FOR_DAY) == FOrdStatus.DONE_FOR_DAY
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.CANCELED) == FOrdStatus.CANCELED
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.PENDING_CANCEL) == FOrdStatus.PENDING_CANCEL
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.STOPPED) == FOrdStatus.STOPPED
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.REJECTED) == FOrdStatus.REJECTED
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.SUSPENDED) == FOrdStatus.SUSPENDED
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.PENDING_NEW) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.CALCULATED) == FOrdStatus.CALCULATED
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.EXPIRED) == FOrdStatus.EXPIRED
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.ACCEPTED_FOR_BIDDING) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.NEW, '8', FExecType.TRADE, FOrdStatus.PENDING_REPLACE) == FOrdStatus.PENDING_REPLACE
    # fmt: on


def test_state_transition__rejected__execution_report():
    # fmt: off
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.CREATED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.PARTIALLY_FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.DONE_FOR_DAY) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.CANCELED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.PENDING_CANCEL) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.STOPPED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.REJECTED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.SUSPENDED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.PENDING_NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.CALCULATED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.EXPIRED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.ACCEPTED_FOR_BIDDING) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.PENDING_REPLACE) == 0
    # fmt: on


def test_state_transition__rejected__execution_report():
    # fmt: off
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.CREATED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.PARTIALLY_FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.DONE_FOR_DAY) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.CANCELED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.PENDING_CANCEL) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.STOPPED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.REJECTED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.SUSPENDED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.PENDING_NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.CALCULATED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.EXPIRED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.ACCEPTED_FOR_BIDDING) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.REJECTED, '8', FExecType.TRADE, FOrdStatus.PENDING_REPLACE) == 0
    # fmt: on


def test_state_transition__filled__execution_report():
    # fmt: off
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.CREATED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.PARTIALLY_FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.DONE_FOR_DAY) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.CANCELED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.PENDING_CANCEL) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.STOPPED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.REJECTED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.SUSPENDED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.PENDING_NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.CALCULATED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.EXPIRED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.ACCEPTED_FOR_BIDDING) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.FILLED, '8', FExecType.TRADE, FOrdStatus.PENDING_REPLACE) == 0
    # fmt: on


def test_state_transition__expired__execution_report():
    # fmt: off
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.CREATED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.PARTIALLY_FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.DONE_FOR_DAY) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.CANCELED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.PENDING_CANCEL) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.STOPPED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.REJECTED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.SUSPENDED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.PENDING_NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.CALCULATED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.EXPIRED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.ACCEPTED_FOR_BIDDING) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.EXPIRED, '8', FExecType.TRADE, FOrdStatus.PENDING_REPLACE) == 0
    # fmt: on


def test_state_transition__canceled__execution_report():
    # fmt: off
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.CREATED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.PARTIALLY_FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.DONE_FOR_DAY) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.CANCELED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.PENDING_CANCEL) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.STOPPED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.REJECTED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.SUSPENDED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.PENDING_NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.CALCULATED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.EXPIRED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.ACCEPTED_FOR_BIDDING) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.CANCELED, '8', FExecType.TRADE, FOrdStatus.PENDING_REPLACE) == 0
    # fmt: on


def test_state_transition__suspended__execution_report():
    # fmt: off
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.CREATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.NEW) == FOrdStatus.NEW
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.PARTIALLY_FILLED) == FOrdStatus.PARTIALLY_FILLED
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.FILLED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.DONE_FOR_DAY) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.CANCELED) == FOrdStatus.CANCELED
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.PENDING_CANCEL) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.STOPPED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.REJECTED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.SUSPENDED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.PENDING_NEW) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.CALCULATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.EXPIRED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.ACCEPTED_FOR_BIDDING) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.SUSPENDED, '8', FExecType.TRADE, FOrdStatus.PENDING_REPLACE) == -23
    # fmt: on


def test_state_transition__partiallyfilled__execution_report():
    # fmt: off
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.CREATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.NEW) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.PARTIALLY_FILLED) == FOrdStatus.PARTIALLY_FILLED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.FILLED) == FOrdStatus.FILLED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.DONE_FOR_DAY) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.CANCELED) == FOrdStatus.CANCELED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.PENDING_CANCEL) == FOrdStatus.PENDING_CANCEL
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.STOPPED) == FOrdStatus.STOPPED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.REJECTED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.SUSPENDED) == FOrdStatus.SUSPENDED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.PENDING_NEW) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.CALCULATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.EXPIRED) == FOrdStatus.EXPIRED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.ACCEPTED_FOR_BIDDING) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PARTIALLY_FILLED, '8', FExecType.TRADE, FOrdStatus.PENDING_REPLACE) == FOrdStatus.PENDING_REPLACE
    # fmt: on


def test_state_transition__pendingcancel__execution_report():
    # fmt: off
    # Executin report doesn't not have any effect of pending cancelled state
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.CREATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.PARTIALLY_FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.DONE_FOR_DAY) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.CANCELED) == FOrdStatus.CANCELED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.PENDING_CANCEL) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.STOPPED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.REJECTED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.SUSPENDED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.PENDING_NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.CALCULATED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.EXPIRED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.ACCEPTED_FOR_BIDDING) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '8', FExecType.TRADE, FOrdStatus.PENDING_REPLACE) == 0

    # But cancel reject request does!
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.CREATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.NEW) == FOrdStatus.NEW
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.PARTIALLY_FILLED) == FOrdStatus.PARTIALLY_FILLED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.FILLED) == FOrdStatus.FILLED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.DONE_FOR_DAY) == FOrdStatus.DONE_FOR_DAY
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.CANCELED) == FOrdStatus.CANCELED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.PENDING_CANCEL) == FOrdStatus.PENDING_CANCEL
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.STOPPED) == FOrdStatus.STOPPED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.REJECTED) == FOrdStatus.REJECTED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.SUSPENDED) == FOrdStatus.SUSPENDED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.PENDING_NEW) == FOrdStatus.PENDING_NEW
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.CALCULATED) == FOrdStatus.CALCULATED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.EXPIRED) == FOrdStatus.EXPIRED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.ACCEPTED_FOR_BIDDING) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_CANCEL, '9', 0, FOrdStatus.PENDING_REPLACE) == FOrdStatus.PENDING_REPLACE
    # fmt: on


def test_state_transition__pendingreplce__execution_report():
    # fmt: off
    # Executin report doesn't not have any effect of pending cancelled state
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.CREATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.PARTIALLY_FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.FILLED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.DONE_FOR_DAY) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.CANCELED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.PENDING_CANCEL) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.STOPPED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.REJECTED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.SUSPENDED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.PENDING_NEW) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.CALCULATED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.EXPIRED) == 0
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.ACCEPTED_FOR_BIDDING) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.TRADE, FOrdStatus.PENDING_REPLACE) == 0
    # fmt: on


def test_state_transition__pendingreplce__execution_report_exectype_replace():
    # fmt: off
    # Executin report doesn't not have any effect of pending cancelled state
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.CREATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.NEW) == FOrdStatus.NEW
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.PARTIALLY_FILLED) == FOrdStatus.PARTIALLY_FILLED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.FILLED) == FOrdStatus.FILLED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.DONE_FOR_DAY) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.CANCELED) == FOrdStatus.CANCELED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.PENDING_CANCEL) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.STOPPED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.REJECTED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.SUSPENDED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.PENDING_NEW) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.CALCULATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.EXPIRED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.ACCEPTED_FOR_BIDDING) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '8', FExecType.REPLACED, FOrdStatus.PENDING_REPLACE) == -23
    # fmt: on


def test_state_transition__pendingreplce__ord_reject():
    # fmt: off
    # But cancel reject request does!
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.CREATED) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.NEW) == FOrdStatus.NEW
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.PARTIALLY_FILLED) == FOrdStatus.PARTIALLY_FILLED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.FILLED) == FOrdStatus.FILLED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.DONE_FOR_DAY) == FOrdStatus.DONE_FOR_DAY
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.CANCELED) == FOrdStatus.CANCELED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.PENDING_CANCEL) == FOrdStatus.PENDING_CANCEL
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.STOPPED) == FOrdStatus.STOPPED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.REJECTED) == FOrdStatus.REJECTED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.SUSPENDED) == FOrdStatus.SUSPENDED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.PENDING_NEW) == FOrdStatus.PENDING_NEW
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.CALCULATED) == FOrdStatus.CALCULATED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.EXPIRED) == FOrdStatus.EXPIRED
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.ACCEPTED_FOR_BIDDING) == -23
    assert FIXNewOrderSingle.change_status(FOrdStatus.PENDING_REPLACE, '9', 0, FOrdStatus.PENDING_REPLACE) == FOrdStatus.PENDING_REPLACE
    # fmt: on


def test_exec_sequence__vanilla_fill():
    """
    A.1.a – Filled order
    https://www.fixtrading.org/online-specification/order-state-changes/#a-vanilla-1

    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )
    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"
    assert o.can_cancel() < 0
    assert o.can_replace() < 0
    assert o.is_finished() == 0

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.PENDING_NEW, f"o.status={chr(o.status)}"
    assert o.can_cancel() < 0
    assert o.can_replace() < 0
    assert o.is_finished() == 0

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.NEW, f"o.status={chr(o.status)}"
    assert o.qty == 10
    assert o.cum_qty == 0
    assert o.leaves_qty == 10

    assert o.can_cancel() > 0
    assert o.can_replace() > 0
    assert o.is_finished() == 0

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.TRADE,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=2,
        leaves_qty=8,
        last_qty=2,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.PARTIALLY_FILLED, f"o.status={chr(o.status)}"
    assert o.qty == 10
    assert o.cum_qty == 2
    assert o.leaves_qty == 8

    assert o.can_cancel() > 0
    assert o.can_replace() > 0
    assert o.is_finished() == 0

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.TRADE,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=3,
        leaves_qty=7,
        last_qty=1,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.PARTIALLY_FILLED, f"o.status={chr(o.status)}"
    assert o.qty == 10
    assert o.cum_qty == 3
    assert o.leaves_qty == 7

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.TRADE,
        FOrdStatus.FILLED,
        cum_qty=10,
        leaves_qty=0,
        last_qty=7,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.FILLED, f"o.status={chr(o.status)}"
    assert o.qty == 10
    assert o.cum_qty == 10
    assert o.leaves_qty == 0

    assert o.can_cancel() < 0
    assert o.can_replace() < 0
    assert o.is_finished() == 1


def test_exec_sequence__vanilla_fill_reject__pendingnew():
    """
    A.1.a – Filled ordern (reject)
    https://www.fixtrading.org/online-specification/order-state-changes/#a-vanilla-1

    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )
    assert o.status == 0, f"o.status={chr(o.status)}"

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.PENDING_NEW, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.REJECTED, FOrdStatus.REJECTED, cum_qty=0, leaves_qty=0
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.REJECTED, f"o.status={chr(o.status)}"
    assert o.qty == 10
    assert o.cum_qty == 0
    assert o.leaves_qty == 00

    assert o.can_cancel() < 0
    assert o.can_replace() < 0
    assert o.is_finished() == 1


def test_exec_sequence__vanilla_fill__reject_new():
    """
    A.1.a – Filled order (reject when new confirmed)
    https://www.fixtrading.org/online-specification/order-state-changes/#a-vanilla-1

    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.PENDING_NEW, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.NEW, f"o.status={chr(o.status)}"
    assert o.qty == 10
    assert o.cum_qty == 0
    assert o.leaves_qty == 10

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.REJECTED, FOrdStatus.REJECTED, cum_qty=0, leaves_qty=0
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.REJECTED, f"o.status={chr(o.status)}"
    assert o.qty == 10
    assert o.cum_qty == 0
    assert o.leaves_qty == 00


def test_exec_sequence__vanilla_suspended():
    """
    A.1.b – Part-filled day order, done for day -> suspended
    https://www.fixtrading.org/online-specification/order-state-changes/#a-vanilla-1

    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.PENDING_NEW, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.NEW, f"o.status={chr(o.status)}"
    assert o.qty == 10
    assert o.cum_qty == 0
    assert o.leaves_qty == 10

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.TRADE,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=2,
        leaves_qty=8,
        last_qty=2,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.PARTIALLY_FILLED, f"o.status={chr(o.status)}"
    assert o.qty == 10
    assert o.cum_qty == 2
    assert o.leaves_qty == 8

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.SUSPENDED,
        FOrdStatus.SUSPENDED,
        cum_qty=2,
        leaves_qty=0,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.SUSPENDED, f"o.status={chr(o.status)}"
    assert o.qty == 10
    assert o.cum_qty == 2
    assert o.leaves_qty == 0

    assert o.can_cancel() > 0
    assert o.can_replace() > 0
    assert o.is_finished() == 0

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.NEW,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=2,
        leaves_qty=8,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.PARTIALLY_FILLED, f"o.status={chr(o.status)}"
    assert o.qty == 10
    assert o.cum_qty == 2
    assert o.leaves_qty == 8


def test_cancel_req():
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.SELL, price=100.0, qty=20
    )
    assert FIXMsg.is_valid(o.msg) == 1
    o.status = FOrdStatus.NEW

    m = o.cancel_req()

    # Tag 11: ClOrdID
    assert m[11] == 0

    # Tag 41: OrigClOrdID
    assert m[41] == o.clord_id

    #  Tag 22: SecurityIDSource - quote cache ticker index
    assert m[22] == 10

    # Tag 38: Order Qty
    assert m[38] == 20

    #  Tag 48: SecurityID - set to instrument_info (uint64_t instrument_id) -- it's going to be stable
    assert m[48] == 123

    # Tag 54: Side
    assert m[54] == "2"  # sell

    #  Tag 55: Symbol set to v2 symbol
    # FIX: assert strcmp(FIXMsg.get_str(m, 55), q.v2_ticker) == 0

    # Tag 60: Transact time
    # FIX: assert timedelta_ns(datetime_nsnow(), FIXMsg.get_utc_timestamp(m, 60)[0], TIMEDELTA_MILLI) < 20

    # Overall message is valid!
    assert FIX_SCHEMA.validate(m)


def test_cancel_req__zero_filled_order():
    """
    B.1.a – Cancel request issued for a zero-filled order
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_cxl_request(o)
    assert o.status == FOrdStatus.PENDING_CANCEL
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.CANCELED, FOrdStatus.CANCELED, cum_qty=0, leaves_qty=0
    )
    assert o.process_execution_report(msg) == 1
    assert o.qty == 10
    assert o.cum_qty == 0
    assert o.leaves_qty == 0

    assert o.can_replace() < 0
    assert o.can_cancel() < 0
    assert o.is_finished() == 1


def test_cancel_req__zero_filled_order__cancel_reject():
    """
    B.1.a – Cancel request issued for a zero-filled order
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.NEW

    cxl_req = ft.fix_cxl_request(o)
    assert o.status == FOrdStatus.PENDING_CANCEL
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0

    msg = ft.fix_cxlrep_reject_msg(cxl_req, FOrdStatus.NEW)
    assert msg.header.msg_type == "9"
    rc = o.process_cancel_rej_report(msg)
    assert rc == 1, rc
    assert o.qty == 10
    assert o.cum_qty == 0
    assert o.leaves_qty == 10
    assert o.status == FOrdStatus.NEW

    assert o.can_replace() > 0
    assert o.can_cancel() > 0
    assert o.is_finished() == 0


def test_cancel_req__zero_filled_order__cancel_reject_after_pending():
    """
    B.1.a – Cancel request issued for a zero-filled order
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_cxl_request(o)
    assert o.status == FOrdStatus.PENDING_CANCEL
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.PENDING_CANCEL,
        FOrdStatus.PENDING_CANCEL,
        cum_qty=0,
        leaves_qty=10,
    )
    assert o.process_execution_report(msg) == 0  # Just ignored!
    assert o.qty == 10
    assert o.cum_qty == 0
    assert o.leaves_qty == 10

    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0

    msg = ft.fix_cxlrep_reject_msg(cxl_req, FOrdStatus.NEW)
    assert msg.header.msg_type == "9"
    rc = o.process_cancel_rej_report(msg)
    assert rc == 1, rc
    assert o.qty == 10
    assert o.cum_qty == 0
    assert o.leaves_qty == 10
    assert o.status == FOrdStatus.NEW

    assert o.can_replace() > 0
    assert o.can_cancel() > 0
    assert o.is_finished() == 0


def test_cancel_req__part_filled_order__with_some_execution_between():
    """
    B.1.b – Cancel request issued for a part-filled order – executions occur whilst cancel request is active
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.TRADE,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=2,
        leaves_qty=8,
        last_qty=2,
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_cxl_request(o)
    assert o.status == FOrdStatus.PENDING_CANCEL
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.TRADE,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=5,
        leaves_qty=5,
        last_qty=3,
    )
    assert o.process_execution_report(msg) == 0
    assert o.status == FOrdStatus.PENDING_CANCEL
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    assert o.qty == 10
    assert o.cum_qty == 5
    assert o.leaves_qty == 5

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.PENDING_CANCEL,
        FOrdStatus.PENDING_CANCEL,
        cum_qty=5,
        leaves_qty=5,
    )
    assert o.process_execution_report(msg) == 0
    assert o.status == FOrdStatus.PENDING_CANCEL
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    assert o.qty == 10
    assert o.cum_qty == 5
    assert o.leaves_qty == 5

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.TRADE,
        FOrdStatus.PENDING_CANCEL,
        cum_qty=6,
        leaves_qty=4,
        last_qty=1,
    )
    assert o.process_execution_report(msg) == 0
    assert o.status == FOrdStatus.PENDING_CANCEL
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    assert o.qty == 10
    assert o.cum_qty == 6
    assert o.leaves_qty == 4

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.CANCELED,
        FOrdStatus.CANCELED,
        cum_qty=6,
        leaves_qty=0,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.CANCELED
    assert o.can_replace() < 0
    assert o.can_cancel() < 0
    assert o.is_finished() == 1
    assert o.qty == 10
    assert o.cum_qty == 6
    assert o.leaves_qty == 0


def test_cancel_req__order_filled_before_cancel_accepted_different_clord():
    """
    B.1.c – Cancel request issued for an order that becomes filled before cancel request can be accepted
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.TRADE,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=2,
        leaves_qty=8,
        last_qty=2,
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_cxl_request(o)
    assert o.status == FOrdStatus.PENDING_CANCEL
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0

    assert o.orig_clord_id > 0
    assert o.clord_id != o.orig_clord_id
    # IMPORTANT: USING OLD CLORD because pretending this report was generated
    # before request for cancel arrived to server
    msg = ft.fix_exec_report_msg(
        o,
        o.orig_clord_id,
        FExecType.TRADE,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=5,
        leaves_qty=5,
        last_qty=3,
    )
    rc = o.process_execution_report(msg)
    assert rc == 0, rc
    assert o.status == FOrdStatus.PENDING_CANCEL
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    assert o.qty == 10
    assert o.cum_qty == 5
    assert o.leaves_qty == 5

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.PENDING_CANCEL,
        FOrdStatus.PENDING_CANCEL,
        cum_qty=5,
        leaves_qty=5,
        last_qty=nan,
        price=nan,
        order_qty=nan,
        orig_clord_id=o.orig_clord_id,
    )
    assert o.process_execution_report(msg) == 0

    msg = ft.fix_exec_report_msg(
        o,
        o.orig_clord_id,
        FExecType.TRADE,
        FOrdStatus.PENDING_CANCEL,
        cum_qty=10,
        leaves_qty=0,
        last_qty=5,
    )
    assert o.process_execution_report(msg) == 0
    assert o.status == FOrdStatus.PENDING_CANCEL
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    assert o.qty == 10
    assert o.cum_qty == 10
    assert o.leaves_qty == 0

    msg = ft.fix_cxlrep_reject_msg(cxl_req, FOrdStatus.FILLED)
    assert o.process_cancel_rej_report(msg) == 1
    assert o.qty == 10
    assert o.cum_qty == 10
    assert o.leaves_qty == 0
    assert o.status == FOrdStatus.FILLED
    assert o.can_replace() < 0
    assert o.can_cancel() < 0
    assert o.is_finished() == 1


def test_cancel_req__not_acknoledged_order_by_gate():
    """
    B.1.c – Cancel request issued for an order that becomes filled before cancel request can be accepted
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    cxl_req = o.cancel_req()
    assert o.can_replace() < 0
    assert o.can_cancel() < 0

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = o.cancel_req()
    assert o.can_replace() < 0
    assert o.can_cancel() < 0


def test_cancel_req__multiple_requests_are_blocked():
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_cxl_request(o)
    assert o.status == FOrdStatus.PENDING_CANCEL
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0


def test_cancel_req__order_filled_before_cancel_accepted():
    """
    B.1.c – Cancel request issued for an order that becomes filled before cancel request can be accepted
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.TRADE,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=2,
        leaves_qty=8,
        last_qty=2,
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_cxl_request(o)
    assert o.status == FOrdStatus.PENDING_CANCEL
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0

    msg = ft.fix_cxlrep_reject_msg(cxl_req, FOrdStatus.REJECTED)
    assert o.process_cancel_rej_report(msg) == 1
    assert o.qty == 10
    assert o.cum_qty == 2
    assert o.leaves_qty == 0
    assert o.status == FOrdStatus.REJECTED
    assert o.can_replace() < 0
    assert o.can_cancel() < 0
    assert o.is_finished() == 1


def test_replace_req():
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.SELL, price=100.0, qty=20
    )
    assert FIXMsg.is_valid(o.msg) == 1
    o.status = FOrdStatus.NEW

    m = o.replace_req(200, 30)

    # Tag 11: ClOrdID
    assert m[11] == 0

    # Tag 41: OrigClOrdID
    assert m[41] == o.clord_id

    #  Tag 22: SecurityIDSource - quote cache ticker index
    assert m[22] == 10

    # Tag 38: Order Qty
    assert m[38] == 30

    # Tag 44: Order Price
    assert m[44] == 200

    #  Tag 48: SecurityID - set to instrument_info (uint64_t instrument_id) -- it's going to be stable
    assert m[48] == 123

    # Tag 54: Side
    assert m[54] == "2"  # sell

    #  Tag 55: Symbol set to v2 symbol
    # FIX: assert strcmp(FIXMsg.get_str(m, 55), q.v2_ticker) == 0

    # Tag 60: Transact time
    # FIX: assert timedelta_ns(datetime_nsnow(), FIXMsg.get_utc_timestamp(m, 60)[0], TIMEDELTA_MILLI) < 20

    # Overall message is valid!
    assert FIX_SCHEMA.validate(m)


def test_replace_req_only_price():
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.SELL, price=100.0, qty=20
    )
    assert FIXMsg.is_valid(o.msg) == 1
    o.status = FOrdStatus.NEW

    m = o.replace_req(200, o.qty)

    # Tag 38: Order Qty
    assert m[38] == 20

    # Tag 44: Order Price
    assert m[44] == 200


def test_replace_req_only_qty():
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.SELL, price=100.0, qty=20
    )
    assert FIXMsg.is_valid(o.msg) == 1
    o.status = FOrdStatus.NEW

    m = o.replace_req(nan, 30)

    # Tag 38: Order Qty
    assert m[38] == 30

    # Tag 44: Order Price
    assert m[44] == 100


def test_replace_req__not_set():
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.SELL, price=100.0, qty=20
    )
    assert FIXMsg.is_valid(o.msg) == 1
    o.status = FOrdStatus.NEW

    m = o.replace_req(nan, nan)
    assert o.last_fix_error == -3

    # No change in price/qty
    m = o.replace_req(o.price, o.qty)
    assert o.last_fix_error == -3

    # No change in price/qty
    m = o.replace_req(o.price, 0)
    assert o.last_fix_error == -3


def test_replace_req__zero_filled__increased_qty():
    """
    C.1.a – Zero-filled order, cancel/replace request issued to increase order qty
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_rep_request(o, 300, 11)
    assert o.status == FOrdStatus.PENDING_REPLACE
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.PENDING_REPLACE,
        FOrdStatus.PENDING_REPLACE,
        cum_qty=0,
        leaves_qty=10,
    )
    assert o.process_execution_report(msg) == 0
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.REPLACED,
        FOrdStatus.NEW,
        cum_qty=0,
        leaves_qty=11,
        last_qty=nan,
        price=300,
        order_qty=11,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.NEW
    assert o.can_replace() > 0
    assert o.can_cancel() > 0
    assert o.is_finished() == 0
    assert o.price == 300
    assert o.qty == 11
    assert o.orig_clord_id == 0


def test_replace_req__part_filled__increased_qty_while_pending_replace_fractional_fill():
    """
    C.1.b – Part-filled order, followed by cancel/replace request to increase order qty, execution occurs whilst order is pending replace
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.TRADE,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=1,
        leaves_qty=9,
        last_qty=1,
    )
    assert o.process_execution_report(msg) == 1
    old_clord = o.clord_id

    cxl_req = ft.fix_rep_request(o, 300, 12)
    assert o.status == FOrdStatus.PENDING_REPLACE
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.PENDING_REPLACE,
        FOrdStatus.PENDING_REPLACE,
        cum_qty=1,
        leaves_qty=9,
    )
    assert o.process_execution_report(msg) == 0
    assert o.status == FOrdStatus.PENDING_REPLACE
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10

    msg = ft.fix_exec_report_msg(
        o,
        o.orig_clord_id,  # ORIG!!!
        FExecType.TRADE,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=1.1,
        leaves_qty=8.9,
        last_qty=0.1,
    )
    assert o.process_execution_report(msg) == 0

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.REPLACED,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=1.1,
        leaves_qty=10.9,
        last_qty=nan,
        price=300,
        order_qty=12,
        orig_clord_id=o.orig_clord_id,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.PARTIALLY_FILLED
    assert o.can_replace() > 0
    assert o.can_cancel() > 0
    assert o.is_finished() == 0
    # Don't change order price/qty until confirmed
    assert o.price == 300
    assert o.qty == 12
    assert o.cum_qty == 1.1
    assert o.leaves_qty == 10.9
    assert o.orig_clord_id == 0
    assert o.clord_id > old_clord

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.TRADE,
        FOrdStatus.FILLED,
        cum_qty=12,
        leaves_qty=0,
        last_qty=10.9,
    )
    assert o.process_execution_report(msg) == 1
    assert o.process_cancel_rej_report(msg) == -3  # WRONG MSG TYPE!
    assert o.status == FOrdStatus.FILLED
    assert o.can_replace() < 0
    assert o.can_cancel() < 0
    assert o.is_finished() == 1
    # Don't change order price/qty until confirmed
    assert o.price == 300
    assert o.qty == 12
    assert o.cum_qty == 12
    assert o.leaves_qty == 0


def test_replace_req__zero_filled__cxlrep_reject_when_new():
    """
    C.1.a – Zero-filled order, cancel/replace request issued, but rejected back to new state
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_rep_request(o, 300, 11)
    assert o.status == FOrdStatus.PENDING_REPLACE
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10

    msg = ft.fix_cxlrep_reject_msg(cxl_req, FOrdStatus.NEW)
    assert o.process_execution_report(msg) == -3  # Wrong MSG type!
    assert o.process_cancel_rej_report(msg) == 1
    assert o.can_replace() > 0
    assert o.can_cancel() > 0
    assert o.is_finished() == 0

    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10


def test_replace_req__filled_order_rejected_after_filled():
    """
    C.1.c – Filled order, followed by cancel/replace request to increase order quantity
    (CASE 1: reject after fill)
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_rep_request(o, 300, 12)
    assert o.status == FOrdStatus.PENDING_REPLACE
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10

    msg = ft.fix_exec_report_msg(
        o,
        o.orig_clord_id,
        FExecType.TRADE,
        FOrdStatus.FILLED,
        cum_qty=10,
        leaves_qty=0,
        last_qty=10,
    )
    assert o.process_execution_report(msg) == 0
    assert o.status == FOrdStatus.PENDING_REPLACE
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10
    assert o.cum_qty == 10
    assert o.leaves_qty == 0

    msg = ft.fix_cxlrep_reject_msg(cxl_req, FOrdStatus.FILLED)
    assert o.process_cancel_rej_report(msg) == 1
    assert o.can_replace() < 0
    assert o.can_cancel() < 0
    assert o.is_finished() == 1

    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10
    assert o.cum_qty == 10
    assert o.leaves_qty == 0


def test_replace_req__filled_order_rejected__filled_increase_passed():
    """
    C.1.c – Filled order, followed by cancel/replace request to increase order quantity
    (CASE 2: fill passed, but following qty increase also passed)
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_rep_request(o, 300, 12)
    assert o.status == FOrdStatus.PENDING_REPLACE
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10

    msg = ft.fix_exec_report_msg(
        o,
        o.orig_clord_id,
        FExecType.TRADE,
        FOrdStatus.FILLED,
        cum_qty=10,
        leaves_qty=0,
        last_qty=10,
    )
    assert o.process_execution_report(msg) == 0
    assert o.status == FOrdStatus.PENDING_REPLACE
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10
    assert o.cum_qty == 10
    assert o.leaves_qty == 0

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.PENDING_REPLACE,
        FOrdStatus.PENDING_REPLACE,
        cum_qty=10,
        leaves_qty=0,
    )
    assert o.process_execution_report(msg) == 0
    assert o.status == FOrdStatus.PENDING_REPLACE
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.REPLACED,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=10,
        leaves_qty=2,
        last_qty=nan,
        price=300,
        order_qty=12,
        orig_clord_id=o.orig_clord_id,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.PARTIALLY_FILLED
    assert o.can_replace() > 0
    assert o.can_cancel() > 0
    assert o.is_finished() == 0

    assert o.price == 300
    assert o.qty == 12
    assert o.cum_qty == 10
    assert o.leaves_qty == 2

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.TRADE,
        FOrdStatus.FILLED,
        cum_qty=12,
        leaves_qty=0,
        last_qty=2,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.FILLED

    assert o.price == 300
    assert o.qty == 12
    assert o.cum_qty == 12
    assert o.leaves_qty == 0


def test_replace_req__replace_price_only_but_rejected_because_fill():
    """
    C.2.a – Cancel/replace request (not for quantity change) is rejected as a fill has occurred
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_rep_request(o, 300, nan)
    assert o.status == FOrdStatus.PENDING_REPLACE
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0

    msg = ft.fix_exec_report_msg(
        o,
        o.orig_clord_id,
        FExecType.TRADE,
        FOrdStatus.FILLED,
        cum_qty=10,
        leaves_qty=0,
        last_qty=10,
    )
    assert o.process_execution_report(msg) == 0
    assert o.status == FOrdStatus.PENDING_REPLACE
    assert o.can_replace() == 0
    assert o.can_cancel() == 0
    assert o.is_finished() == 0
    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10
    assert o.cum_qty == 10
    assert o.leaves_qty == 0

    msg = ft.fix_cxlrep_reject_msg(cxl_req, FOrdStatus.FILLED)
    assert o.process_cancel_rej_report(msg) == 1
    assert o.can_replace() < 0
    assert o.can_cancel() < 0
    assert o.is_finished() == 1

    # Don't change order price/qty until confirmed
    assert o.price == 200
    assert o.qty == 10
    assert o.cum_qty == 10
    assert o.leaves_qty == 0


def test_replace_req__decreased_qty():
    """
    C.3.a – Cancel/replace request sent whilst execution is being reported –
    the requested order qty exceeds the cum qty. Order is replaced then filled
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.TRADE,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=2,
        leaves_qty=8,
        last_qty=2,
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_rep_request(o, nan, 9)
    assert o.status == FOrdStatus.PENDING_REPLACE

    msg = ft.fix_exec_report_msg(
        o,
        o.orig_clord_id,
        FExecType.TRADE,
        FOrdStatus.PENDING_REPLACE,
        cum_qty=3,
        leaves_qty=7,
        last_qty=1,
    )
    assert o.process_execution_report(msg) == 0
    assert o.status == FOrdStatus.PENDING_REPLACE

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.REPLACED,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=3,
        leaves_qty=6,
        last_qty=nan,
        price=200,
        order_qty=9,
        orig_clord_id=o.orig_clord_id,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.PARTIALLY_FILLED
    assert o.can_replace() > 0
    assert o.can_cancel() > 0
    assert o.is_finished() == 0

    assert o.price == 200
    assert o.qty == 9
    assert o.cum_qty == 3
    assert o.leaves_qty == 6


def test_replace_req__decreased_qty_exact_match_to_fill():
    """
    C.3.b – Cancel/replace request sent whilst execution is being reported –
    the requested order qty equals the cum qty – order qty is amended to cum qty
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_rep_request(o, nan, 7)
    assert o.status == FOrdStatus.PENDING_REPLACE

    msg = ft.fix_exec_report_msg(
        o,
        o.orig_clord_id,
        FExecType.TRADE,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=7,
        leaves_qty=3,
        last_qty=7,
    )
    assert o.process_execution_report(msg) == 0

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.REPLACED,
        FOrdStatus.FILLED,
        cum_qty=7,
        leaves_qty=0,
        last_qty=nan,
        price=200,
        order_qty=7,
        orig_clord_id=o.orig_clord_id,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.FILLED
    assert o.can_replace() < 0
    assert o.can_cancel() < 0
    assert o.is_finished() == 1

    assert o.price == 200
    assert o.qty == 7
    assert o.cum_qty == 7
    assert o.leaves_qty == 0


def test_replace_req__decreased_qty__also_less_than_cum_qty():
    """
    C.3.c – Cancel/replace request sent whilst execution is being reported –
    the requested order qty is below cum qty – order qty is amended to cum qty
    :return:
    """
    o = FIXNewOrderSingle(
        "clordTest", "US.F.TICKER", side=FOrdSide.BUY, price=200.0, qty=10
    )

    ft = FIXTester()
    assert ft.order_register_single(o) == 1
    assert o.status == FOrdStatus.CREATED, f"o.status={chr(o.status)}"

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.PENDING_NEW, FOrdStatus.PENDING_NEW
    )
    assert o.process_execution_report(msg) == 1

    msg = ft.fix_exec_report_msg(
        o, o.clord_id, FExecType.NEW, FOrdStatus.NEW, cum_qty=0, leaves_qty=10
    )
    assert o.process_execution_report(msg) == 1

    cxl_req = ft.fix_rep_request(o, nan, 7)
    assert o.status == FOrdStatus.PENDING_REPLACE

    msg = ft.fix_exec_report_msg(
        o,
        o.orig_clord_id,
        FExecType.TRADE,
        FOrdStatus.PARTIALLY_FILLED,
        cum_qty=8,
        leaves_qty=2,
        last_qty=8,
    )
    assert o.process_execution_report(msg) == 0

    msg = ft.fix_exec_report_msg(
        o,
        o.clord_id,
        FExecType.REPLACED,
        FOrdStatus.FILLED,
        cum_qty=8,
        leaves_qty=0,
        last_qty=nan,
        price=200,
        order_qty=8,
        orig_clord_id=o.orig_clord_id,
    )
    assert o.process_execution_report(msg) == 1
    assert o.status == FOrdStatus.FILLED
    assert o.can_replace() < 0
    assert o.can_cancel() < 0
    assert o.is_finished() == 1

    assert o.price == 200
    assert o.qty == 8
    assert o.cum_qty == 8
    assert o.leaves_qty == 0
