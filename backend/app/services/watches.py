"""Opt-in corpus-change inbox. No email sending and no claim to monitor the whole web."""
from sqlalchemy import select
from ..models import Watch, Source, Subscription, Notification, now
from .entitlements import access
from .retrieval import score


def check_watches(db, config):
    if not config.enable_experimental_agents:
        return 0
    count = 0
    for watch in db.scalars(select(Watch).where(Watch.enabled.is_(True), Watch.next_at <= now())
                            .with_for_update(skip_locked=True).limit(50)):
        if not access(db.get(Subscription, watch.user_id), config)['agent_allowed']:
            watch.next_at = now() + 86400
            continue
        sources = db.scalars(select(Source).where(Source.enabled.is_(True), Source.reviewed.is_(True),
                                                  Source.created_at > watch.last_source_at)).all()
        hits = [s for s in sources if score(watch.topic, s.title) > 0]
        if hits:
            db.add(Notification(user_id=watch.user_id, watch_id=watch.id,
                    title=f'New approved sources: {watch.topic}'[:200],
                    body='The approved platform corpus has new source records. Applicability is not determined.\n' +
                    '\n'.join(f'{s.title} ({s.id})' for s in hits[:20])))
            count += 1
        watch.last_source_at = now()
        watch.next_at = now() + watch.cadence_days * 86400
    db.commit()
    return count
