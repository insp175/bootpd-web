def cleared_leases(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS cleared_leases(ip TEXT, mac TEXT, expiry INTEGER, PRIMARY KEY(ip,mac))"
    )
    return set(db.execute("SELECT ip,mac,expiry FROM cleared_leases"))


def signature(lease):
    return lease["ip"], lease["mac"], lease["expiry"]


def visible_leases(db, leases, now):
    cleared = cleared_leases(db)
    return [
        lease for lease in leases
        if lease["expiry"] > now or signature(lease) not in cleared
    ]


def clear_expired(db, leases, now):
    cleared = cleared_leases(db)
    expired = [signature(lease) for lease in leases if lease["expiry"] <= now]
    db.executemany(
        "INSERT INTO cleared_leases VALUES(?,?,?) ON CONFLICT(ip,mac) DO UPDATE SET expiry=excluded.expiry",
        expired,
    )
    db.commit()
    return len(set(expired) - cleared)
