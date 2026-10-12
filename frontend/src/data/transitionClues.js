// Physical Transition Round — static clue data (frontend prototype only).
//
// Every clue points to a physical destination in the real venue; the website only displays the text.
// Destination/zone names are intentionally NOT stored here: players must work them out.
// Clue wording is supplied by the event organizers and must not be edited, paraphrased or
// re-wrapped. Each `text` keeps the original line breaks (render with `whitespace-pre-line`).
// Replace this module with an API call when a backend exists; the shape is the contract.

// Zone ids are internal only (grouping/assignment). Zone names and destinations are never
// shown to players: they must work out where to go from the clue text itself.
export const ZONE_ORDER = ['past', 'present', 'future'];

export const CLUES_BY_ZONE = {
  past: [
    {
      number: 1,
      text: `Before silicon learned to carry entire worlds,
information slept inside a fragile square shell.
Seek the device that once guarded files
with only a fraction of today’s memory.`,
    },
    {
      number: 2,
      text: `Enter the age before screens became windows to thought.
Where metal keys struck paper one letter at a time,
and every mistake demanded patience rather than a click.
Find the machine that gave words their physical form.`,
    },
    {
      number: 3,
      text: `Before displays became thin enough to disappear,
images lived behind thick glass and glowing tubes.
Search the era where entertainment arrived
inside a heavy box that ruled the living room.`,
    },
    {
      number: 4,
      text: `Before contacts lived inside glowing rectangles,
voices travelled through wires and numbered dials.
Find the device where every digit required
a deliberate journey around a circular path.`,
    },
    {
      number: 5,
      text: `Before streaming carried entire libraries through the air,
stories slept upon magnetic tape.
Seek the age where a small plastic cassette
could bring an entire movie back to life.`,
    },
    {
      number: 6,
      text: `Before pixels replaced chemicals and memory became instant,
moments waited patiently inside rolls of hidden film.
Find the device that captured light
and demanded development before revealing the past.`,
    },
    {
      number: 7,
      text: `Before messages appeared instantly on glowing screens,
a silent little device waited for a signal.
It could tell you that someone was searching for you,
but could not carry the conversation any further.`,
    },
    {
      number: 8,
      text: `Before the network became silent and invisible,
connection arrived with a storm of electronic noise.
Find the gateway that sang its strange mechanical song
before opening the door to the early digital world.`,
    },
    {
      number: 9,
      text: `Before songs lived inside pockets and clouds,
music travelled on a shining circular surface.
Seek the machine that transformed
a spinning disc of stored data into sound.`,
    },
    {
      number: 10,
      // Supplied heading for this clue: "HARDER / MORE CHRONOS-LIKE". It is an organizer note,
      // kept with the data but not shown on the participant-facing clue card.
      organizerNote: 'HARDER / MORE CHRONOS-LIKE',
      text: `Travel backward beyond wireless signals and instant memory.
Find the era where information had weight,
communication demanded patience,
and machines announced their presence with clicks, spins, and static.`,
    },
  ],

  present: [
    {
      number: 1,
      text: `Between the dust of early gears and the neon of unborn centuries lies your target.
Walk toward the territory where silicon breathes alongside you, pocket-sized glass holds the map, and silent batteries rule the road.
Find the middle ground of the timeline.`,
    },
    {
      number: 2,
      text: `Too sophisticated for punch cards, yet too grounded for warp drives and chrome cities.
Follow the trail where rotors take flight with a flick of a thumb, plastic solidifies layer by layer, and machines complete your half-written thoughts.
Target the chapter you walk through every single day.`,
    },
    {
      number: 3,
      text: `Step past the museum of ancient circuits, but halt before you stumble into sci-fi lore.
Your objective is circled by ambient signals, wristbands reading heartbeats through the skin, and unseen servers catching every falling file.
Seek the space that mirrors your active reality.`,
    },
    {
      number: 4,
      text: `Leave behind the click-clack of the telegraph and avoid the teleportation bays ahead.
You are hunting for the hub where cables were cut, twin acoustic pebbles sit in your ears, and virtual dimensions rest right across your brow.
Locate the central station.`,
    },
    {
      number: 5,
      text: `Neither archaeological relic nor a dream yet to be coded.
Head toward the domain where prompt becomes image in the blink of an eye, and portable drives slip off keychains into waiting ports.
Lock onto the anchor between yesterday and tomorrow.`,
    },
    {
      number: 6,
      text: `Look for the floor where engines whisper instead of roar and four rotors survey the grounds from above.
It is the only coordinate on the map where today's routine feels like yesterday’s fantasy.
Find the heartbeat of the modern campus.`,
    },
    {
      number: 7,
      text: `Bypass the genesis of transistors and turn your back on the interstellar frontier.
Navigate to where coordinate slices melt into solid objects and algorithmic mirrors reflect human text.
Step straight into the median sector.`,
    },
    {
      number: 8,
      text: `The mechanical dials have vanished, but the cybernetic implants haven't arrived.
You will find this territory marked by glowing slates, invisible cloud racks, and devices that count your daily strides.
Converge upon the living epoch.`,
    },
    {
      number: 9,
      text: `A bridge spanning two extremes: one of forgotten copper coils, the other of sentient androids.
Search for the outpost where touchscreens wake with a glance and code paints pictures before your coffee gets cold.
Your stop is the center of the spectrum.`,
    },
    {
      number: 10,
      text: `Not buried under the sands of history, and not drifting in the haze of deep space.
Head to where wireless frequencies weave through the air and synthetic minds answer the call of a single line of text.
Claim the sector standing dead center.`,
    },
  ],

  future: [
    {
      number: 1,
      text: `Before you trace the lines of steel and wire,
You must align the clock of future fire.
Find where the time-drift starts its rapid spin,
And enter first to let the quest begin.`,
    },
    {
      number: 2,
      text: `Where wheels roll forward with no human guide,
Search the vehicle bay where sensors hide.
Look underneath the chassis of the machine,
To lift the veil of what remains unseen.`,
    },
    {
      number: 3,
      text: `A silent sentinel stands watch in white,
Its metallic chest concealing code from sight.
Unlatch the casing where the joints align,
To extract the fragment of the core design.`,
    },
    {
      number: 4,
      text: `Past glowing screens where silent thoughts connect,
A terminal awaits your intellect.
Do not touch keys, but trace the neural stream,
To crack the code within the waking dream.`,
    },
    {
      number: 5,
      text: `A mini-metropolis of flashing light,
Where data pathways weave through endless night.
Check block sector four beneath the tower base,
Where urban logic locks the security place.`,
    },
    {
      number: 6,
      text: `In frost-locked chambers where the qubits freeze,
You cannot pass with ordinary keys.
Superpose the numbers in the cooling phase,
To clear the barrier of the binary maze.`,
    },
    {
      number: 7,
      text: `High up in zero-gravity designs,
Where orbital fabrication softly shines.
Inspect the cargo crate marked ‘void-approved’,
To find the piece that time and tide unmoved.`,
    },
    {
      number: 8,
      text: `An active firewall blocks the final stair,
Broadcasting warning signals through the air.
Bypass the logic loop with sequence strain,
To drop the shield across the central main.`,
    },
    {
      number: 9,
      text: `Encrypted fragments float in buffer space,
Scattered like stardust across the network base.
Reconstruct the bytes before the buffers bleed,
And parse the text with absolute dispatch and speed.`,
    },
    {
      number: 10,
      text: `The three epochs converge upon this spot:
The past, the present, and what time forgot.
Combine the final code with future might,
And break the lock to flood the room with light.`,
    },
  ],
};

// Flat list in ZONE_ORDER x clue order. The backend assigns each team a `clue_id` (0..29) that
// indexes into this list; the zone itself is never sent to or shown by the client.
export const CLUE_LIST = ZONE_ORDER.flatMap((zoneId) => CLUES_BY_ZONE[zoneId]);

export function getClueById(clueId) {
  return CLUE_LIST[clueId] || null;
}
