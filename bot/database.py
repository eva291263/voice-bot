from datetime import date, datetime, timezone
import secrets
import string

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select, func

import config
from bot.models import Base, Referral, Transcription, User

engine = create_async_engine(
    config.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=10,
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def _today_str() -> str:
    return date.today().isoformat()


def _gen_referral_code(length=8) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    referred_by_code: str | None = None,
) -> tuple[User, bool]:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    created = False

    if user is None:
        referrer_id = None
        bonus = 0.0
        if referred_by_code:
            ref_result = await session.execute(
                select(User).where(User.referral_code == referred_by_code)
            )
            referrer = ref_result.scalar_one_or_none()
            if referrer and referrer.telegram_id != telegram_id:
                referrer_id = referrer.telegram_id
                bonus = float(config.TRIAL_BONUS_MINUTES)

        code = _gen_referral_code()
        while True:
            existing = await session.execute(select(User).where(User.referral_code == code))
            if existing.scalar_one_or_none() is None:
                break
            code = _gen_referral_code()

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            referral_code=code,
            referred_by=referrer_id,
            trial_minutes_remaining=float(config.TRIAL_MINUTES) + bonus,
        )
        session.add(user)
        try:
            await session.flush()
        except Exception:
            await session.rollback()
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
            if user:
                if username and user.username != username:
                    user.username = username
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                await session.commit()
            return user, False

        if referrer_id:
            ref_entry = Referral(
                referrer_telegram_id=referrer_id,
                referred_telegram_id=telegram_id,
            )
            session.add(ref_entry)

        await session.commit()
        created = True
    else:
        if username and user.username != username:
            user.username = username
        if first_name and user.first_name != first_name:
            user.first_name = first_name
        await session.commit()

    return user, created


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


def reset_daily_if_needed(user: User) -> None:
    today = _today_str()
    if user.daily_reset_date != today:
        user.daily_minutes_used = 0.0
        user.daily_reset_date = today


def get_available_minutes(user: User) -> float:
    reset_daily_if_needed(user)
    if user.is_pro:
        return max(0.0, config.PRO_MONTHLY_MINUTES - user.pro_minutes_used)
    if not user.trial_exhausted:
        return max(0.0, user.trial_minutes_remaining + user.bonus_minutes)
    return max(0.0, config.DAILY_FREE_MINUTES - user.daily_minutes_used + user.bonus_minutes)


def deduct_minutes(user: User, minutes: float) -> None:
    reset_daily_if_needed(user)
    if user.is_pro:
        user.pro_minutes_used = user.pro_minutes_used + minutes
        return
    if not user.trial_exhausted:
        if user.trial_minutes_remaining >= minutes:
            user.trial_minutes_remaining -= minutes
        else:
            remaining = minutes - user.trial_minutes_remaining
            user.trial_minutes_remaining = 0.0
            if user.bonus_minutes >= remaining:
                user.bonus_minutes -= remaining
            else:
                user.bonus_minutes = 0.0
        if user.trial_minutes_remaining <= 0 and user.bonus_minutes <= 0:
            user.trial_exhausted = True
    else:
        if user.bonus_minutes >= minutes:
            user.bonus_minutes -= minutes
        else:
            remaining = minutes - user.bonus_minutes
            user.bonus_minutes = 0.0
            user.daily_minutes_used += remaining


async def add_transcription(
    session: AsyncSession, user: User, text: str, duration_seconds: float
) -> Transcription:
    t = Transcription(
        user_id=user.id,
        telegram_id=user.telegram_id,
        text=text,
        duration_seconds=duration_seconds,
    )
    session.add(t)
    deduct_minutes(user, duration_seconds / 60.0)
    await session.commit()
    return t


async def get_transcription_history(
    session: AsyncSession, user: User, limit: int = 10
) -> list[Transcription]:
    max_records = 100 if user.is_pro else 5
    effective_limit = min(limit, max_records)
    result = await session.execute(
        select(Transcription)
        .where(Transcription.telegram_id == user.telegram_id)
        .order_by(Transcription.created_at.desc())
        .limit(effective_limit)
    )
    return list(result.scalars().all())


async def get_transcription_by_id(
    session: AsyncSession, transcription_id: int, telegram_id: int
) -> Transcription | None:
    result = await session.execute(
        select(Transcription).where(
            Transcription.id == transcription_id,
            Transcription.telegram_id == telegram_id,
        )
    )
    return result.scalar_one_or_none()


async def delete_transcription(session: AsyncSession, transcription: Transcription) -> None:
    await session.delete(transcription)
    await session.commit()


async def activate_pro(session: AsyncSession, user: User) -> None:
    from datetime import timedelta
    user.is_pro = True
    user.pro_expires_at = datetime.now(timezone.utc).replace(
        hour=23, minute=59, second=59
    ) + __import__("datetime").timedelta(days=30)
    user.pro_period_start = datetime.now(timezone.utc)
    user.pro_minutes_used = 0.0
    await session.commit()


async def add_bonus_minutes(
    session: AsyncSession, user: User, minutes: float, is_pro_user: bool = False
) -> None:
    reset_daily_if_needed(user)
    if not is_pro_user:
        current_bonus = user.referral_bonus_this_month
        can_add = max(0.0, config.MAX_REFERRAL_BONUS_MINUTES_FREE - current_bonus)
        actual_add = min(minutes, can_add)
        user.bonus_minutes += actual_add
        user.referral_bonus_this_month += actual_add
    else:
        user.pro_minutes_used = max(0.0, user.pro_minutes_used - minutes)
    await session.commit()


async def mark_referral_successful(session: AsyncSession, referred_telegram_id: int) -> int | None:
    result = await session.execute(
        select(Referral).where(
            Referral.referred_telegram_id == referred_telegram_id,
            Referral.is_successful == False,
        )
    )
    ref = result.scalar_one_or_none()
    if ref is None:
        return None
    ref.is_successful = True
    await session.commit()
    return ref.referrer_telegram_id


async def get_referral_stats(session: AsyncSession, telegram_id: int) -> dict:
    total_result = await session.execute(
        select(func.count(Referral.id)).where(Referral.referrer_telegram_id == telegram_id)
    )
    success_result = await session.execute(
        select(func.count(Referral.id)).where(
            Referral.referrer_telegram_id == telegram_id,
            Referral.is_successful == True,
        )
    )
    total = total_result.scalar() or 0
    successful = success_result.scalar() or 0
    return {"total": total, "successful": successful}


async def delete_user_data(session: AsyncSession, user: User) -> None:
    result = await session.execute(
        select(Transcription).where(Transcription.telegram_id == user.telegram_id)
    )
    for t in result.scalars().all():
        await session.delete(t)
    await session.delete(user)
    await session.commit()
