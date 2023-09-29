import pytest

from asyncfix.errors import FIXMessageError, DuplicateSeqNoError
from asyncfix.connection import MessageDirection
from asyncfix.journaler import Journaler
from asyncfix.message import FIXContainer, FIXMessage
from asyncfix.session import FIXSession


def test_create_or_load():
    j = Journaler()

    s1 = j.create_or_load('test_target', 'test_sender')
    assert isinstance(s1, FIXSession)
    assert s1.sender_comp_id == 'test_sender'
    assert s1.target_comp_id == 'test_target'
    assert s1.snd_seq_num == 0
    assert s1.next_expected_msg_seq_num == 1
    assert s1.key == 1
    
    s2 = j.create_or_load('test_target', 'test_sender')
    assert isinstance(s1, FIXSession)
    assert s2.sender_comp_id == 'test_sender'
    assert s2.target_comp_id == 'test_target'
    assert s2.snd_seq_num == 0
    assert s2.next_expected_msg_seq_num == 1
    assert s2.key == 1

    assert s1 is not s2


def test_find_seqno():
    enc_msg = b"8=FIX.4.4\x019=75\x0135=D\x0149=sender\x0156=target\x0134=073\x0152=20230919-07:13:26.808\x0144=123.45\x0138\x0155=VOD.L\x0110=100\x01"  # noqa
    assert Journaler.find_seq_no(enc_msg) == 73

    with pytest.raises(FIXMessageError):
        enc_msg = b"8=FIX.4.4\x019=75\x0135=D\x0149=sender\x0156=target\x0134=\x0152=20230919-07:13:26.808\x0144=123.45\x0138\x0155=VOD.L\x0110=100\x01"  # noqa
        Journaler.find_seq_no(enc_msg)

    with pytest.raises(FIXMessageError):
        enc_msg = b"8=FIX.4.4\x019=75\x0135=D\x0149=sender\x0156=target\x0152=20230919-07:13:26.808\x0144=123.45\x0138\x0155=VOD.L\x0110=100\x01"  # noqa
        Journaler.find_seq_no(enc_msg)

    with pytest.raises(FIXMessageError):
        enc_msg = b"8=FIX.4.4\x019=75\x0135=D\x0149=sender\x0156=target\x0134=asdf\x0152=20230919-07:13:26.808\x0144=123.45\x0138\x0155=VOD.L\x0110=100\x01"  # noqa
        Journaler.find_seq_no(enc_msg)

    
def test_persist():
    enc_msg = b"8=FIX.4.4\x019=75\x0135=D\x0149=sender\x0156=target\x0134=073\x0152=20230919-07:13:26.808\x0144=123.45\x0138\x0155=VOD.L\x0110=100\x01"  # noqa
    assert Journaler.find_seq_no(enc_msg) == 73

    j = Journaler()
    s1 = j.create_or_load('test_target', 'test_sender')
    assert s1.snd_seq_num == 0
    assert s1.next_expected_msg_seq_num == 1

    # persist and reload rewrites session seq num
    j.persist_msg(enc_msg, s1, MessageDirection.INBOUND)
    s2 = j.create_or_load('test_target', 'test_sender')

    assert s2.next_expected_msg_seq_num == 74
    assert s2.snd_seq_num == 0

    j.persist_msg(enc_msg, s1, MessageDirection.OUTBOUND)

    s2 = j.create_or_load('test_target', 'test_sender')

    assert s2.next_expected_msg_seq_num == 74
    assert s2.snd_seq_num == 73

    with pytest.raises(DuplicateSeqNoError, match="73 is a duplicate"):
        j.persist_msg(enc_msg, s1, MessageDirection.OUTBOUND)


def test_sessions():
    enc_msg = b"8=FIX.4.4\x019=75\x0135=D\x0149=sender\x0156=target\x0134=073\x0152=20230919-07:13:26.808\x0144=123.45\x0138\x0155=VOD.L\x0110=100\x01"  # noqa
    assert Journaler.find_seq_no(enc_msg) == 73

    j = Journaler()
    s1 = j.create_or_load('test_target', 'test_sender')
    s2 = j.create_or_load('test_target2', 'test_sender2')

    # persist and reload rewrites session seq num
    j.persist_msg(enc_msg, s1, MessageDirection.INBOUND)

    sessions = j.sessions()
    assert isinstance(sessions, dict)
    assert ('test_target', 'test_sender') in sessions
    assert s1 in sessions

    s_new = j.create_or_load('test_target', 'test_sender')
    assert s_new in sessions

def test_persist_recover():
    enc_msg = b"8=FIX.4.4\x019=75\x0135=D\x0149=sender\x0156=target\x0134=073\x0152=20230919-07:13:26.808\x0144=123.45\x0138\x0155=VOD.L\x0110=100\x01"  # noqa
    assert Journaler.find_seq_no(enc_msg) == 73

    j = Journaler()
    s1 = j.create_or_load('test_target', 'test_sender')
    # persist and reload rewrites session seq num
    j.persist_msg(enc_msg, s1, MessageDirection.INBOUND)
    j.persist_msg(enc_msg, s1, MessageDirection.OUTBOUND)

    s2 = j.create_or_load('test_target', 'test_sender')
    assert s2.next_expected_msg_seq_num == 74
    assert s2.snd_seq_num == 73

    m = j.recover_msg(s2, MessageDirection.INBOUND, 73)
    assert m == enc_msg

    m2 = j.recover_msg(s2, MessageDirection.INBOUND, 173)
    assert m2 is None


def test_get_all_msg():
    enc_msg_in = b"8=FIX.4.4\x019=75\x0135=D\x0149=sender\x0156=target\x0134=073\x0152=20230919-07:13:26.808\x0144=123.45\x0138\x0155=VOD.L\x0110=100\x01"  # noqa
    enc_msg_out = b"8=FIX.4.4\x019=75\x0135=D\x0149=sender\x0156=target\x0134=078\x0152=20230919-07:13:26.808\x0144=123.45\x0138\x0155=VOD.L\x0110=100\x01"  # noqa

    j = Journaler()
    s1 = j.create_or_load('test_target', 'test_sender')
    s2 = j.create_or_load('test_target2', 'test_sender2')
    # persist and reload rewrites session seq num
    j.persist_msg(enc_msg_in, s1, MessageDirection.INBOUND)
    j.persist_msg(enc_msg_out, s1, MessageDirection.OUTBOUND)

    all = j.get_all_msgs()
    assert len(all) == 2
    assert all[0] == (73, enc_msg_in, MessageDirection.INBOUND.value, 1)
    assert all[1] == (78, enc_msg_out, MessageDirection.OUTBOUND.value, 1)

    all = j.get_all_msgs(sessions=[s1])
    assert len(all) == 2
    assert all[0] == (73, enc_msg_in, MessageDirection.INBOUND.value, 1)
    assert all[1] == (78, enc_msg_out, MessageDirection.OUTBOUND.value, 1)

    all = j.get_all_msgs(sessions=[s2])
    assert len(all) == 0

    all = j.get_all_msgs(sessions=[s1], direction=MessageDirection.INBOUND)
    assert len(all) == 1
    assert all[0] == (73, enc_msg_in, MessageDirection.INBOUND.value, 1)

    all = j.get_all_msgs(sessions=[s1], direction=MessageDirection.OUTBOUND)
    assert len(all) == 1
    assert all[0] == (78, enc_msg_out, MessageDirection.OUTBOUND.value, 1)
