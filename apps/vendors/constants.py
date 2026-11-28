"""String values shared by the vendors slice (views, selectors, tests)."""

VENDOR_ROLE = "VENDOR"

APPLICATION_PENDING = "PENDING"
APPLICATION_APPROVED = "APPROVED"
APPLICATION_REJECTED = "REJECTED"
APPLICATION_WITHDRAWN = "WITHDRAWN"
# WAITLISTED is added to BoothApplication.Status (with a migration) in B3.
APPLICATION_WAITLISTED = "WAITLISTED"

# Statuses that still count as a live application (withdrawable, block a duplicate).
ACTIVE_APPLICATION_STATUSES = (
    APPLICATION_PENDING,
    APPLICATION_APPROVED,
    APPLICATION_WAITLISTED,
)