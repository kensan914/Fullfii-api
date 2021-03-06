from django.db.models import Q
from django.utils import timezone
from account.models import Status
from chat.models import Room, TalkStatus


def end_talk_v2(room, ender, is_time_out=False):
    """
    v2. トークを終了するときに1回だけ実行. set talked_accounts.
    :param room:
    :param ender:
    :return:
    """
    room.is_end = True
    room.ended_at = timezone.now()
    room.is_time_out = is_time_out
    room.save()

    if not ender:
        return

    speaker = room.speaker_ticket.owner

    # 相手方(終了させられた方)のtalkticketをfinishing状態に
    should_finish_ticket = room.listener_ticket if speaker.id == ender.id else room.speaker_ticket
    should_finish_ticket.status = TalkStatus.FINISHING
    should_finish_ticket.save()


def end_talk_ticket(talk_ticket):
    talk_ticket.status = TalkStatus.WAITING
    talk_ticket.wait_start_time = timezone.now()  # reset wait_start_time
    talk_ticket.save()


def end_talk(room, is_first_time, user):
    """
    only v1.
    トークを終了するときにリクエストユーザ、レスポンスユーザで2回実行. roomレコードの変更
    :param room:
    :param is_first_time: 初めてならTrue. 既にroomのend処理がなされていたらFalse
    :param user
    :return:
    """
    # end talk for the first time
    if is_first_time:
        room.is_end = True
        room.ended_at = timezone.now()

    # turn on is_end_(req or res)
    if user.id == room.request_user.id:
        room.is_end_request = True
    else:
        room.is_end_response = True
    room.save()


def change_status_of_talk(room, user_id=None):
    """
    only v1.
    トークを終了するときに一度だけ実行. ユーザのstatusを変更
    :param room:
    :param user_id:
    :return:
    """
    room_members = [room.request_user, room.response_user]
    me = None

    for user in room_members:
        talking_rooms = Room.objects.exclude(id=room.id).filter(
            Q(request_user__id=user.id) | Q(response_user_id=user.id), is_start=True, is_end=False)
        if not talking_rooms.exists():
            if user.is_online:
                user.status = Status.ONLINE
            else:
                user.status = Status.OFFLINE
            user.save()
            if user_id is not None and user.id == user_id:
                me = user

    if me is not None:
        return me
