---
okf_version: "0.2"
type: note
title: "Preference center sketch — notification preference defaults"
tier: raw
initiative: NOVA
created: "2026-08-08"
updated: "2026-08-08"
created_by: SP
updated_by: SP
status: ACTIVE
tags: [nova, notifications, preferences, defaults, ui]
---

# Preference center sketch — notification preference defaults

Sketch notes for the notification preference surface. The whole screen is really an argument about notification preference defaults, so the defaults are written down first and the pixels second.

## The notification preference defaults table

Every row below is the default a brand-new user gets with no stored preference row at all. These defaults are what the screen renders before the user has any preferences.

| Notification category | Default channel | Default cadence | Default state |
|---|---|---|---|
| Assigned to me | in-app + email | immediate | on by default |
| Direct reply | in-app + email | immediate | on by default |
| Card I own blocked | in-app | daily digest | on by default |
| Due date changed | in-app | daily digest | on by default |
| Watched board activity | in-app | daily digest | off by default |
| Anything I did myself | none | none | off by default, not overridable |

## Notes on the defaults

The default posture is quiet. Two categories interrupt by default; three roll into the daily digest by default; one is off by default. The last row is not a preference at all — self-caused events are suppressed unconditionally, so it renders as a disabled row with an explanation rather than a toggle, otherwise a user will flip it on, hate it, and blame the defaults.

The digest cadence default is daily. A per-user cadence preference exists (off / four-hourly / daily / weekly) but the default is daily because the research says a daily roll-up is the shape people described.

## Rendering a user with no preferences

Important implementation note for WS-3: do not write a preference row on first render. A user with no stored preferences renders the defaults from the table above, and only a real toggle writes anything. This keeps "reset to defaults" a delete rather than a migration, and it keeps a later change to the default table applying to everyone who never touched their preferences.

## Screen shape

Three stacked sections: Categories (one row per notification category, with the default shown as ghost text when unmodified), Digest (cadence preference plus a delivery-hour preference), Quiet hours (a start and end time, default off).

Every toggle is a real focusable control. A "Reset to defaults" action sits at the bottom of each section and clears the stored preferences for that section only.

## Open

Do quiet hours suppress or defer? SP's preference is defer, TN's preference is suppress. Not resolved in this sketch.
