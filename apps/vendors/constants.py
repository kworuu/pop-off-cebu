"""String values shared by the vendors slice (views, selectors, tests)."""

VENDOR_ROLE = "VENDOR"

APPLICATION_PENDING = "PENDING"
APPLICATION_APPROVED = "APPROVED"
APPLICATION_REJECTED = "REJECTED"
APPLICATION_WITHDRAWN = "WITHDRAWN"
# Added to BoothApplication.Status in B3 (vendors migration 0002).
APPLICATION_WAITLISTED = "WAITLISTED"

# Statuses that still count as a live application (withdrawable, block a duplicate).
ACTIVE_APPLICATION_STATUSES = (
    APPLICATION_PENDING,
    APPLICATION_APPROVED,
    APPLICATION_WAITLISTED,
)