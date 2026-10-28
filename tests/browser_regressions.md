# Browser regression checks

Use the supported CUA browser controls against the running local server. Use pointer
clicks, rather than Enter, for the handbook close test: keyboard activation did not
reproduce the original overlap defect.

## Handbook and entry

With the local game tab bound as `tab`, run this CUA JavaScript:

```javascript
await tab.playwright.getByRole('button', {name: 'How to play ↗', exact: true}).click();
await tab.playwright.getByRole('button', {name: 'Close ✕', exact: true}).click();
const open = await tab.playwright.evaluate(
  () => document.querySelector('#rules').hasAttribute('open')
);
if (open) throw Error('REGRESSION: handbook Close leaves the modal open');
```

The original page failed this check. A DOM hit test at the button center returned
`#modal-guide`, because a positioned content block painted above the floated button.
The fix separates the modal header and scrolling content and uses a native
`method="dialog"` form for dismissal.

Also check Close after scrolling to the bottom of the handbook, at desktop and
phone widths. Pointer-click Play demo with a blank nickname: it must immediately
start a lesson as Chef Trainee. Create a room must show nickname/difficulty/bots;
Join a room must show only nickname/code. Check XXX-XXX automatic formatting and
joining a second device with a raw/lowercase code. Invalid code feedback must
appear beside the entry controls. There are four total chef slots, including bots.

## Exit guard

In a demo or real game, click Back to homepage and verify Leave this kitchen appears.
Choose Keep cooking: the kitchen and session must remain. Repeat, choose Leave game,
and verify the lobby appears. The header logo must use the same confirmation.
Escape should dismiss the confirmation without leaving. Test in fullscreen too.

Close/reload/navigation uses `beforeunload`: supported browsers show their own generic
warning after user interaction. An embedded browser may suppress this prompt. The
webpage cannot guarantee interception of the enclosing desktop application's exit.
Canceling navigation must not send a leave request or release the player slot.

## Results and rematch

Join one room in two independent tabs and let service finish. Each tab must open a
results dialog with the same frozen score, target, win/loss, and statistics. This is
cooperative: a winning crew shares the victory; a loss has no winning player.

The host can click Rematch setup, review the difficulty/crew, then apply the restart; guests see a disabled rematch button and host guidance.
A host rematch must close the results in both tabs, reset score/statistics, and start
one new round with both players still present. Dismissing the dialog must not make
it reopen on each state poll. View results reopens it on demand.

For demos, check automatic results on a correct service or timeout, Retry sample
round, Next demo round, and the final Finish demo action. Results-to-home must also
ask for confirmation. Win/loss/statistics/rematch resets are covered without waiting
for real time by `python -m unittest discover -s tests -p test_results.py`.

## Bots, game-only fullscreen, sound, and throws

Create an Easy kitchen with two bots, start service, and verify both BOT labels move
through recipe phases, wash plates, and produce positive service points without
human cooking. Verify the host can configure bots before/between rounds, guests
cannot, and the four-chef cap includes bots. `test_bots.py` simulates all recipes
and three bots without waiting for real time.

In a real round, enter fullscreen and verify only the restaurant game canvas,
labelled HUD/tickets, and small Menu button appear. No gameplay action bar,
keyboard-instruction footer, or disabled Service live button belongs in the canvas.
The HUD must have its own row above the canvas, with the map name visible:
read the bounding rectangles and assert `.arena-hud.bottom <= #canvas.top` in
normal/fullscreen and phone-sized layouts. Previously this failed by 66 pixels.
The clean/dirty plate count must appear in the dining-room DISH RETURN panel, with an accessible #supply count inside the arena but outside the HUD. The interaction popup must be
small and in a bottom corner. The handbook/configuration/crew sidebar must be
outside the fullscreen target. `#game-alerts` must be a descendant of `#arena`.
Trigger a food-ready alert or an invalid interaction and verify it stays inside
the fullscreen game bounds. Open Menu for commands, sound, fullscreen exit, and
Leave kitchen confirmation. The sidebar must not duplicate the plating instructions.
Demo fullscreen should still include its lessons.

Toggle sound off/on. On entry, the visible on state should correspond to a resumed
audio context. After refreshing a joined game, Enable sound should resume it.
Listen for the music, soft/urgent clock, washing water, food-ready chime, and fire
alarm. A visual state check does not verify subjective audio volume/quality.

Collect an ingredient, face an open space, and throw: the former empty-counter
restriction must not apply. Aim by clicking the canvas, throw toward another chef,
with full hands and verify a visible flight, 1.25-second movement stun, and recoverable landed food.
Repeat with empty hands: the recipient must catch the food, with no stun or duplicate
floor item. Bots catch too and deposit the item on a counter before resuming work.
Moving again must clear mouse aim. Check keyboard movement after an invalid
button interaction too; focus must not trap WASD on the action button.
Throw through the middle of an empty counter/stove and verify an in-flight catch;
near misses and occupied surfaces must not snap the projectile onto them. Suitable
prepared food starts cooking on a stove; other caught food can be retrieved.

## Shared pause and surprises

Join two clients, wait through the launch countdown, and open Menu as host. Both clocks and the bot
must stop; guest Resume is disabled. Leave paused while doing another check, then
verify the clock is identical before resuming. Both clients resume together with
preserved cooking, ticket and task time. Test P and fullscreen pause controls too.

In Medium, the first counter-shuffle warning arrives after 28 seconds of unpaused
play, followed by a three-second countdown and 1.4-second station exchange. Check
matching announcement text on both clients, food/plates travelling with the station,
and bot navigation continuing afterward. Higher difficulties add stove shuffles,
steam and combined rushes; Easy has visual-only interruptions. Pause during a warning
and verify its countdown also freezes. Demos must not get surprise events. Controls,
tickets and critical alerts remain above the effects. The pause/shuffle unit tests
cover timing and inventory without relying on browser wall-clock waits.

## Special guests and soundtrack

Start a real kitchen: the third ticket must be a gold VIP with explicit bonus and
failure amounts, mirrored by a crowned dining-room guest and fullscreen ticket.
Medium and above later alternate purple Critic/VIP visits; the guest count and
stakes scale with difficulty. Verify served/missed metrics in results and that a
guest left at the buzzer deducts its penalty before determining a team win.
Demo kitchens have no special visitors. `test_vip.py` covers score outcomes and limits.

The `#kitchen-music` audio element must load the uploaded Cyborg Ninja MP3, loop,
and advance during live service. It must pause when shared-paused, muted, hidden,
or finished; resume preserves position, while rematch resets position. Verify the
sound button and visible media-error feedback; never substitute synthesized music
after a loading failure. Kitchen effects should still run beside the soundtrack.

On Medium wait for ingredient crates to move; on Expert verify prep/service swaps;
Chef de Cuisine begins with a kitchen station carousel; Serve must remain at its customer-facing position while other stations move. Warning highlights
must match the moving objects. Station labels, food, cook timers, and bot routes
follow the same station identities; plate supply remains intact.

## Host menu, launch, and reconnect checks

Before starting, the host alone sees start/settings commands. Start a real round
and verify both clients show Aprons on / 3 / 2 / 1 / GO in sync. Round time stays
at 4:00, tickets keep their full patience, and chefs/bots cannot move before launch.
The host's menu must show restart/end commands with confirmation; guests must not
see them. Restart gives the entire crew a new countdown. End shows results to all.
After dismissing results, open Menu and leave it open over several state polls;
it must not immediately close. View results must still work inside the menu.

The URL must include the room code after creating/joining/rejoining. Open a fresh
page in the same browser and verify the saved-session prompt offers Rejoin / Not
now / Forget. Rejoin must restore the same chef rather than allocate a new slot.
For multiple test tabs, per-tab records take priority over the last origin-wide
local-storage record. Never print or screenshot private storage/token values.

A connection interruption must show a retry/rejoin choice and suspend local input.
The room continues on the server unless paused. If the room has been removed or
the server restarted, a rejoin attempt must show an explicit unavailable-session
message and offer Forget. Explicit Leave must clear that chef's saved record and
the room query from the URL. Authentication tokens must not appear in public
state snapshots or room URLs; public IDs do not authorize host commands.

## Timer escalation and visual load

The HUD clock contains digits only (no visible Time prefix). Above 30 seconds it is
yellow; at 30 it gets the clock-urgent red blink. At 10 through 1 seconds, LAST CALL
and a large red clock appear centrally, with pointer-events:none and the HUD clock
hidden. The central clock must clear for shared pause, results, restart, and leave.
Pause freezes urgency animation; reduced motion shows static red warnings.
`node tests/test_timer.cjs` covers 31/30/11/10/1/0 thresholds and lifecycle states.
For the browser check, let an untouched demo run toward its three-minute limit and
inspect #arena-time and #last-call at both thresholds; then check the same UI in
real-game fullscreen. No development endpoint or shortened production round is needed.

Chefs retain names and held-food icons but no carried-item boxes, task captions, or
floating bot-job text. Verify clean/dirty numbers below the customer queue and that
Serve stays beside the customers after prep swaps and carousel motion. Burn-window
values must agree between room setup, handbook, server settings, and README.

## Shutdowns, drinks, dining, and restart setup

Create Medium with bots and join a human guest. Drinks must appear in the kitchen,
sidebar, pause-menu recipes, and eligible ticket pool. A bot or human must mix a
cup for three seconds and serve it at the wall-attached Serve window (13,4),
approaching from (12,4). Verify points, a seated dining customer, and unchanged
plate supply for a drink. There are four server-assigned chairs and twelve-second
dining time; shared pause freezes occupancy time.

The pause menu must list humans/bots/host, delivered orders, all available recipes,
score/target/tickets/seats, and the two shutdown conditions. Guests see the details
but cannot issue host actions. Restart opens difficulty and checked-crew options.
Uncheck a guest and a bot, choose Easy, and confirm: one new shared countdown, the
selected roster, recalculated target, and no Drinks station/recipe. The removed
guest must return home with an explanation and cleared saved session. Restart can
also configure a new shift after a shutdown. Invalid selections must not partially
change the room; host cannot remove themselves.

Unit tests drive exact score-floor, fire-warning/expiry, just-in-time extinguish,
pause deadline, and frozen-result boundaries. A real round reaching −200 must show
Kitchen shut down with that reason; a stove burning for twenty seconds must show
the fire reason even above target. The central fire countdown clears on extinguish,
pause, results, or restart. Demo lessons remain forgiving.
